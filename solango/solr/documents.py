#
# Copyright 2008 Optaros, Inc.
#

"""
A generic search system which allows configuration of
search document options on a per-model basis.

To use, do two things:

1. Create or import a subclass of ``SearchDocument`` defining the
    options you want.

2. Import ``searchdocument`` from this module and register one or more
    models, passing the models and the ``SearchDocument`` options
    class you want to use.


Example
-------

First, we define a simple model class which might represent entries in
a weblog::
    
    from django.db import models
    
    class Post(models.Model):
        title = models.CharField(maxlength=250)
        body = models.TextField()
        pub_date = models.DateField()
        enable_comments = models.BooleanField()

Then we create a `SearchDocument` subclass specifying some
moderation options::
    
import solango
    
class PostDocument(solango.SearchDocument):
    content = solango.fields.TextField(copy=True)
    
    #Overrides the default transform
    def transform_content(self, instance):
        return instance.body

And finally register it for searching:
    solango.register(Post, PostDocument)
"""

from django.utils.datastructures import SortedDict
from django.db.models.base import ModelBase, Model
from django.forms.models import model_to_dict
from django.template.loader import render_to_string

from solango import fields as search_fields
from solango.solr import get_model_from_key
from solango import settings

from copy import deepcopy

__all__ = ('SearchDocumentBase', 'SearchDocument')

class NoPrimaryKeyFieldException(Exception):
    pass

def get_model_declared_fields(bases, attrs, with_base_fields=True):
    """
    Taken from NewForms
    """
    Meta = attrs.get('Meta', None)
    model = getattr(Meta, 'model', None)
    fields = []
    if isinstance(model, ModelBase):
        for field in model._meta.fields:
            try:
                search_field = getattr(search_fields, field.__class__.__name__)
                fields.append((field.attname, search_field(dynamic=True)),)
            except Exception, e:
                pass
    fields.extend([(field_name, attrs.pop(field_name)) for field_name, obj in attrs.items() if isinstance(obj, search_fields.Field)])
    fields.sort(lambda x, y: cmp(x[1].creation_counter, y[1].creation_counter))

    # If this class is subclassing another Form, add that Form's fields.
    # Note that we loop over the bases in *reverse*. This is necessary in
    # order to preserve the correct order of fields.
    if with_base_fields:
        for base in bases[::-1]:
            if hasattr(base, 'base_fields'):
                fields = base.base_fields.items() + fields
    else:
        for base in bases[::-1]:
            if hasattr(base, 'declared_fields'):
                fields = base.declared_fields.items() + fields
    
    for name, field in fields:
        field.name = name
    
    media = attrs.get('Media', None)
    template = getattr(media, 'template', None)
    if template:
        attrs['template'] = template
    
    return SortedDict(fields)


class DeclarativeFieldsMetaclass(type):
    """
    Taken from NewForms
    """
    def __new__(cls, name, bases, attrs):
        attrs['base_fields'] = get_model_declared_fields(bases, attrs)
        new_class = super(DeclarativeFieldsMetaclass,
                     cls).__new__(cls, name, bases, attrs)
        return new_class

class BaseSearchDocument(object):
    def __init__(self, arg):
        """
        Takes a model, dict, or tuple.
        
        for a model it assumes that you are trying to create a document from the values
        
        for a dict it assumes that you recieved results from solr and you want to make a 
        python object representation of the model    
        
        For a tuple of the form (model_key, instance_id), it creates a document
        from the corresponding model instance. if the instance does not exist, it
        will succeed. This is useful for creating documents to remove from the
        index, after the instance has already been deleted.
            
        """
        
        self.fields = deepcopy(self.base_fields)
        self.pk_field = None
        self._model = None
        self.data_dict = {}
        self.highlight = ""
        self.boost = ""
        self._transformed = False
        self._is_deleted = False

        # If it's a model, set the _model and create a dictionary from the fields
        if isinstance(arg, Model):
            #make it into a dict.
            self._model = arg
            self.data_dict = model_to_dict(arg)
        elif isinstance(arg, dict):
            self.data_dict = arg
        elif isinstance(arg, (tuple, list)):
            if len(arg) != 2:
                raise ValueError('Tuple argument must be of the form (model_key, instance_id)')
            
            model = get_model_from_key(arg[0])
            try:
                self._model = model.objects.get(pk=arg[1])
            except model.DoesNotExist:
                self._is_deleted = True
        else:
            raise ValueError('Argument must be a Model, a dictionary or a tuple')
        
        # Iterate through fields and get value
        for field in self.fields.values():
            #Save value
            if isinstance(field, search_fields.PrimaryKeyField):
                self.pk_field = field
                break
        
        if not self.pk_field:
            raise NoPrimaryKeyFieldException('Search Document needs a Primary Key Field')
        
        if self._model:
            self._transform_field(self.pk_field)
            self.boost = self.get_boost(self._model)
        elif self.data_dict:
            self.clean()
            self._transformed = True
            self.boost = self.get_boost(self.get_model_instance())
        else:
            self.pk_field.value = self.pk_field.make_key(arg[0], arg[1])
    
    def __getitem__(self, name):
        "Convenience method for templates"
        try:
            field = self.fields[name]
        except KeyError:
            raise KeyError('Key %r not found in Form' % name)
        return field.value

    def _transform_field(self, field):
        value = None
        try:
            value = getattr(self, 'transform_%s' % field.name)(self._model)
            field.value = value
        except AttributeError:
            #no transform rely on the field
            field.transform(self._model)

    def transform(self):
        """
        Takes an model instance and transforms it into a Search Document
        """
        if not self._model:
            raise ValueError('No model to transform into a Search Document')
        
        if not self._transformed:
            for field in self.fields.values():
                if field != self.pk_field:
                    self._transform_field(field)
            self._transformed = True
    
    def clean(self):
        """
        Takes the data dictionary and creates python values from it.
        """
        
        if not self.data_dict:
            raise ValueError('No data dict to create python values from')

        for name, field in self.fields.items():
            # Key Errors were being thrown here if the document expected a field
            # that wasn't returned.
            if self.data_dict.has_key(field.get_name()):
                field.value = self.data_dict[field.get_name()]
                try:
                    value = None
                    value = getattr(self, 'clean_%s' % name, None)()
                    field.value = value
                except Exception, e:
                    #no transform rely on the field
                    field.clean()
            else:
                # field not found in Solr's response,
                # assume field was null when indexed
                field.value = None
    
    def __unicode__(self):
        """
        Returns the Solr document XML representation of this Document.
        """
        return self.to_xml()
    
    def delete(self):
        return self.to_xml(True)
    
    def add(self):
        if self.is_indexable(self._model):
            return self.to_xml()
        else:
            return ''
    
    def to_xml(self, delete=False):
        doc = None
        if delete:
            #Delete looks like <id>1</id>
            doc = u"<id>%s</id>" % (self.pk_field.value,)
        else:
            self.transform()
            doc = u"".join([unicode(field) for field in self.fields.values()])
            
            if self.boost:
                boost_attr = ' boost="%s"' % self.boost
            else:
                boost_attr = ''
            
            doc = u"<doc%s>\n%s</doc>\n" % (boost_attr, doc)
        
        return doc

    def render_html(self):
        return render_to_string(self.template, {'document' : self})
    
    def is_indexable(self, instance):
        """
        If true then the instance is indexed
        """
        return True
    
    def is_deleted(self):
        """
        If the document was created with a tuple (model_key, instance_id)
        and the model instance no longer exists, returns True.
        """
        return self._is_deleted

    def get_model_instance(self):
        """
        Returns the model instance that the document refers to.
        """
        if self.data_dict:
            model = get_model_from_key(self.data_dict['model'])
            id = self.data_dict['id'].split(settings.SEARCH_SEPARATOR)[2]
            
            return model.objects.get(pk=id)
        elif self._model:
            return self._model
        return None

    def get_boost(self, instance):
        """
        Override this to specify a custom per-document boost.
        """
        return ''

class SearchDocument(BaseSearchDocument):
    id      = search_fields.PrimaryKeyField()
    model   = search_fields.ModelField()
    site_id = search_fields.SiteField()
    url     = search_fields.UrlField()
    text    = search_fields.SolrTextField(multi_valued=True)    
    
    class Media:
        template = 'solango/default_document.html'
        
    __metaclass__ = DeclarativeFieldsMetaclass
