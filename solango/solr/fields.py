#
# Copyright 2008 Optaros, Inc.
#

import re
from  datetime import datetime, date
from time import strptime
from django.utils.encoding import smart_unicode

from django.conf import settings as django_settings
from solango import conf
from solango.solr import get_instance_key
from solango.solr import utils


__all__ = ["Field", "DateField", "DateTimeField", "CharField", "TextField", 
           "IntegerField", "BooleanField", "UrlField", "SiteField", 
           "ModelField", "FloatField", "DoubleField", "LongField"]

class Field(object):
    """
    Field
    -----
    An abstraction for a Search Document field.
    
    ..attribute: name
        
        Name of field
    
    ..attribute: value
    
        Value of field
        
    ..attribute: copy
    
        Boolean, if true the value will be copied into the field(s) specified
        in 'dest'. Default value is False

    ..attribute: dest
    
        String, Tuple or List: solr field(s) name where field value should be
        copied. Default value is "text".

    ..attribute: dynamic
    
        Boolean, if field is created on the fly this lets us tell solr where it 
        needs to end up. By default dynamic fields are copied into the text 
        field. Default value is `False`
    
    ..attribute: indexed 
    
        Boolean, If (and only if) a field is indexed, then it is searchable, 
        sortable, and facetable. Default value is `True`
    
    ..attribute: stored
    
        Boolean, `True` if the value of the field should be retrievable during
        a search. Default value is `True`
    
    ..attribute: boost
    
        Float, Index the field with a custom boost. Default value is `None`.
    
    """
    # Tracks each time a Field instance is created. Used to retain order.
    creation_counter = 0
    
    def __init__(self, name='', value=None, required=False, copy=False, 
                dest="text", dynamic=False, indexed=True, stored=True, 
                multi_valued=False, omit_norms=False, boost=None, 
                extra_attrs={}):
        
        self.name = smart_unicode(name)
        self.value = value
        self.copy = copy
        self.dynamic = dynamic
        self.indexed = indexed
        self.multi_valued = multi_valued
        self.stored = stored
        self.extra_attrs = extra_attrs

        if isinstance(dest, basestring):
            dest = [dest]

        self.omit_norms = omit_norms
        self.dest = dest
        self.required = required
        self.boost = boost
        
        # Increase the creation counter, and save our local copy.
        self.creation_counter = Field.creation_counter
        Field.creation_counter += 1
        
        # Highlighting used on display, if a doc value has highlighted field it
        # can be displayed by calling self.highlight
        self.highlight = None
                
    def __unicode__(self):
        
        if not self.multi_valued:
            return self._create_field_xml()

        values = self.value
        if not isinstance(values, (list, tuple)):
            values = [values]

        results = []
        for value in values:
            if value is None:
                results.append('')
            else:
                results.append(self._create_field_xml(value))

        return '\n'.join(results)

    def _create_field_xml(self, value=None):
        if value is None:
            value = self.value
        
        if value is None or value == '':
            return ''
        
        boost_attr = ''
        if self.boost:
            boost_attr = ' boost="%s"' % self.boost
        
        value = self.from_python(value)
        
        xml = '<field name="%s"%s>%s</field>\n' % (self.get_name(), 
                                                   boost_attr, value)
        return xml

    def dynamic_name(self):
        return "%s_%s" % (self.name, self.dynamic_suffix)
    
    def get_name(self):
        if self.dynamic:
            return self.dynamic_name()
        else:
            return self.name
    
    def transform(self, model):
        try:
            self.value = getattr(model, self.name)
        except AttributeError, e:
            #not all fields like 'text' will have a transform.
            pass
    
    def _config(self):
        """
        Used by the command to generate the solr config document
        """
        return '<field name="%s" type="%s" indexed="%s" stored="%s" omitNorms="%s" required="%s" multiValued="%s"/>' \
            % (self.name, self.type, str(self.indexed).lower(), str(self.stored).lower(), \
                   str(self.omit_norms).lower(), str(self.required).lower(), str(self.multi_valued).lower())
        
    def _config_copy(self):
        pattern = '<copyField source="%s" dest="%%s"/>' % self.name
        return '\n'.join((pattern % dest for dest in self.dest))
    
    def clean(self):
        """
        If the transform messed up the data this is a way of getting it back to normal
        """
        if isinstance(self.value, list) and self.multi_valued is False:
            self.value = ' '.join(self.value)
    
    def highlighting(self, limit=100):
        """
        Used in the template
        
        if the document has a highlight value, return it, else fall back on the default value
        """
        if self.highlight:
            return self.highlight
        
        return self.value[:limit]
    
    def from_python(self, value):
        return unicode(value)
    
class DateField(Field):
    dynamic_suffix = "dt"
    type = "date"
    
    def clean(self):
        if isinstance(self.value, datetime):
            self.value = self.value.date()
        elif isinstance(self.value, unicode):
            self.value = datetime(*strptime(self.value, "%Y-%m-%dT%H:%M:%SZ")[0:6]).date()
    
    def from_python(self, value):
        if isinstance(value, date):
            return value.strftime('%Y-%m-%dT00:00:00.000Z')
        return ""
        
class DateTimeField(Field):
    dynamic_suffix = "dt"
    type = "date"

    def clean(self):
        if isinstance(self.value, unicode):
            self.value = datetime(*strptime(self.value, "%Y-%m-%dT%H:%M:%SZ")[0:6])

    def from_python(self, value):
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        return ""

class CharField(Field):
    dynamic_suffix = "s"
    type = "string"
    
class TextField(Field):
    dynamic_suffix = "t"
    type="text"
    
class SolrTextField(Field):
    dynamic_suffix = "t"
    type="text"
        
    def transform(self, model):
        pass

class IntegerField(Field):
    dynamic_suffix = "i"
    type = "integer"
    
    def clean(self):
        if isinstance(self.value, list):
            self.value = [int(i) for i in self.value]        
        elif self.value is not None and not isinstance(self.value, int):
            self.value = int(self.value)
        
class BooleanField(Field):
    dynamic_suffix = "b"
    type = "boolean"
    
    def clean(self):
        if not isinstance(self.value, bool):
            if self.value == 'true':
                self.value = True
            elif self.value == 'false':
                self.value = False
    
    def from_python(self, value):
        if value is True:
            return "true"
        elif value is False: 
            return "false"
        else:
            return ""
    
class UrlField(CharField):
    
    def __init__(self, *args, **kwargs):
        super(UrlField, self).__init__(name='url', *args, **kwargs)
    
    def transform(self, model):
        """
        If the model has a `get_absolute_url` method use it.
        """
        try:
            self.value = model.get_absolute_url()
        except AttributeError:
            self.value = ""
        return unicode(self)

class PrimaryKeyField(CharField):
    
    def __init__(self, *args, **kwargs):
        kwargs.update({'required' : True})
        super(PrimaryKeyField, self).__init__(*args, **kwargs)
    
    def make_key(self, model_key, pk):
        return "%s%s%s" % (model_key, conf.SEARCH_SEPARATOR, pk)
        
    def transform(self, instance):
        """
        Returns a unique identifier string for the specified object.
        
        This avoids duplicate documents
        """
        self.value = self.make_key(get_instance_key(instance), instance.pk)
        
        return unicode(self)
    
    def clean(self):
        self.value = self.value.split(conf.SEARCH_SEPARATOR)[-1]

class SiteField(IntegerField):
    def __init__(self, *args, **kwargs):
        kwargs.update({'required' : True})
        super(SiteField, self).__init__( *args, **kwargs)

    def transform(self, value_or_model):
        self.value = django_settings.SITE_ID
        return unicode(self)

class ModelField(CharField):
   
    def __init__(self, *args, **kwargs):
        kwargs.update({'required' : True})
        super(ModelField, self).__init__(name='id', *args, **kwargs)

    def transform(self, instance):
        self.value = get_instance_key(instance)
        return unicode(self)

class FloatField(Field):
    dynamic_suffix = "f"
    type = "float"
    
    def clean(self):
        if not isinstance(self.value, float):
            self.value = float(self.value)

class DoubleField(Field):
    dynamic_suffix = "d"
    type = "double"
    
    def clean(self):
        if not isinstance(self.value, float) and not self.muti_valued:
            self.value = float(self.value)
        
class LongField(Field):
    dynamic_suffix = "l"
    type = "long"

    def clean(self):
        if not isinstance(self.value, long) and not self.muti_valued:
            self.value = long(self.value)
