#
# Copyright 2008 Optaros, Inc.
#

import re
from  datetime import datetime
from time import strptime
from django.utils.encoding import smart_unicode
from django.conf import settings as django_settings
from solango import settings
from solango.solr import get_model_key
from solango.solr import utils

class Field(object):
    """
    An abstraction for a Search Document field.
    
    name    -- Name  of field 
    value   -- Value of field
    
    copy -- Boolean, if true the value will be copied into the field(s) specied
    in 'dest'

    dest -- String, Tuple or List: solr field(s) name where field value should
    be copied. Defaults to "text".

    dynamic -- Boolean, if field is created on the fly lets us tell solr where it 
        needs to end up. by default dynamic fields are copyied into the text field
    
    indexed -- If (and only if) a field is indexed, then it is searchable, sortable, 
        and facetable.
    
    stored=true|false
        True if the value of the field should be retrievable during a search
    
    boost -- Index the field with a custom boost.
    
    """
    # Tracks each time a Field instance is created. Used to retain order.
    creation_counter = 0
    
    def __init__(self, name='', value=None, required=False, copy=False, dest="text", dynamic=False, indexed=True, stored=True,
                multi_valued=False, omit_norms=False, boost=None, extra_attrs={}):
        self.name = smart_unicode(name)
        
        self.value,  self.copy, self.dynamic, self.indexed = value, copy, dynamic, indexed
        self.multi_valued, self.stored, self.extra_attrs = multi_valued, stored, extra_attrs

        if isinstance(dest, basestring):
            dest = [dest]

        self.omit_norms, self.dest, self.required = omit_norms, dest, required
        self.boost = boost
        
        # Increase the creation counter, and save our local copy.
        self.creation_counter = Field.creation_counter
        Field.creation_counter += 1
        
        # highlighting
        # Used on display, if a doc value has highlighted field it can be displayed by calling
        # self.highlight
        self.highlight = None
        
        # Clean the field value of tags and other nasty things.  Unfortunately,
        # we can't use sax or dom to do this elegantly, because often the 
        # fields which look like XML are not well-formed.
        if value:
            value = str(value.replace("<![CDATA[", "").replace("]]>", ""))
            self.value = unicode(re.sub(r"<[^>]*?>", "", value), "utf-8")
        
    def __unicode__(self):
        result = []
        values = self.value

        if not self.multi_valued \
            or self.multi_valued and not isinstance(values, (list, tuple)):
            values = [values]

        for value in values:
            value = utils._from_python(value)
            if value is not None:
                if self.boost:
                    boost_attr = ' boost="%s"' % self.boost
                else:
                    boost_attr = ''
                    
                xml = '<field name="%s"%s><![CDATA[%s]]></field>\n'
                result.append(xml % (self.get_name(), boost_attr, value))
            else:
                result.append('')

        if self.multi_valued:
            return '\n'.join(result)

        return result[0]

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
        if isinstance(self.value, list):
            self.value = ' '.join(self.value)
    
    def highlighting(self, limit=100):
        """
        Used in the template
        
        if the document has a highlight value, return it, else fall back on the default value
        """
        if self.highlight:
            return self.highlight
        
        return self.value[:limit]
    
class DateField(Field):
    dynamic_suffix = "dt"
    type = "date"
    
    def clean(self):
        if isinstance(self.value, datetime):
            self.value = self.value.date()
        elif isinstance(self.value, unicode):
            self.value = datetime(*strptime(self.value, "%Y-%m-%dT%H:%M:%SZ")[0:6]).date()
    
class DateTimeField(Field):
    dynamic_suffix = "dt"
    type = "date"

    def clean(self):
        if isinstance(self.value, unicode):
            self.value = datetime(*strptime(self.value, "%Y-%m-%dT%H:%M:%SZ")[0:6])

class CharField(Field):
    dynamic_suffix = "s"
    type = "string"
    
    def clean(self):
        super(CharField, self).clean()
        self.value = unicode(self.value)

class TextField(Field):
    dynamic_suffix = "t"
    type="text"
    
    def clean(self):
        super(TextField, self).clean()
        self.value = unicode(self.value)

class SolrTextField(Field):
    dynamic_suffix = "t"
    type="text"
    
    def clean(self):
        super(SolrTextField, self).clean()
        self.value = unicode(self.value)
    
    def transform(self, model):
        pass

class IntegerField(Field):
    dynamic_suffix = "i"
    type = "integer"
    
    def clean(self):
        if isinstance(self.value, list):
            self.value = [int(i) for i in self.value]
        elif not isinstance(self.value, int):
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
        return "%s%s%s" % (model_key, settings.SEARCH_SEPARATOR, pk)
        
    def transform(self, model):
        """
        Returns a unique identifier string for the specified object.
        
        This avoids duplicate documents
        """
        self.value = self.make_key(get_model_key(model), model.pk)
        
        return unicode(self)
    
    def clean(self):
        self.value = self.value.split(settings.SEARCH_SEPARATOR)[-1]

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

    def transform(self, value_or_model):
        self.value = get_model_key(value_or_model)
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
        if not isinstance(self.value, float):
            self.value = float(self.value)
        
class LongField(Field):
    dynamic_suffix = "l"
    type = "long"

    def clean(self):
        if not isinstance(self.value, long):
            self.value = long(self.value)
