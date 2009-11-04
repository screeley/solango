#
# Copyright 2008 Optaros, Inc.
#

"""
Will handle the base wrapper.

"""

from django.db.models.loading import get_model
from django.forms.forms import DeclarativeFieldsMetaclass, BaseForm
from django.db.models.base import ModelBase
from solango import conf

#Helper Functions for getting and setting models
#The type field sets the value as app_label__module_name

def get_instance_key(instance):
    """
    May be one of many things, a Model, a Form or a Dictionary.
    """
    #model
    if isinstance(instance, ModelBase) or \
        isinstance(instance.__class__, ModelBase):
        return u'%s%s%s' % (instance._meta.app_label, 
                            conf.SEARCH_SEPARATOR, 
                            instance._meta.module_name)
    
    #Form
    elif isinstance(instance, DeclarativeFieldsMetaclass):
        part = conf.SEARCH_SEPARATOR.join(instance.__module__.split("."))
        return u'%s%s%s' % (part, conf.SEARCH_SEPARATOR,  
                            instance.__name__.lower())
        
    elif isinstance(instance, BaseForm):
        part = conf.SEARCH_SEPARATOR.join(instance.__module__.split("."))
        return u'%s%s%s' % (part, conf.SEARCH_SEPARATOR,  
                            instance.__class__.__name__.lower())
    
    #Instance Dictionary / Dictionary
    elif isinstance(instance, (UserDict, dict)) and instance.has_key("model"):
        return instance["model"]
    
    raise AttributeError("Needs to be either a Form or a Model")

def get_model_from_key(type):
    app_label, module_name = type.split(conf.SEARCH_SEPARATOR)
    return get_model(app_label, module_name)
