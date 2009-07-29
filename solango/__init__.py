#
# Copyright 2008 Optaros, Inc.
#
# django_settings so when we do  solango import settings we don't get confused
from django.conf import settings as django_settings
from django.db.models import signals
from django.db.models.base import ModelBase

registry = {}

#Fields so we can do run things like solango.CharField
from solango.solr import fields
from solango.solr import get_model_key
from solango.solr.connection import SearchWrapper
from solango.solr.documents import SearchDocument
from solango.indexing import indexer

class AlreadyRegistered(Exception):
    pass

class NotRegistered(Exception):
    pass

connection = SearchWrapper()
SearchDocument = SearchDocument

def register(model_or_iterable, search_document=None, connect_signals=True):
    if isinstance(model_or_iterable, ModelBase):
        model_or_iterable = [model_or_iterable]
    for model in model_or_iterable:
        #Register the model
        if model in registry:
            raise AlreadyRegistered('%s has already been registered by search' % model)
        if not search_document:
            #Default Search Document if no document is specified.
            search_document = SearchDocument
        key = get_model_key(model)
        registry[key] = search_document
        if connect_signals:
            #Hook Up The Signals
            signals.post_save.connect(indexer.post_save, model)
            signals.post_delete.connect(indexer.post_delete, model)

for a in django_settings.INSTALLED_APPS:
    try:
        """
        This will call all the fun things in the search documents
        """
        module = __import__(a + '.search', {}, {}, [''])
    except ImportError, e:
        pass

def get_document(instance_or_tuple):
    """
    Helper to get document from either model instance,
    or tuple in the form (model_key, instance_id)
    """
    if isinstance(instance_or_tuple, tuple):
        key = instance_or_tuple[0]
    else:
        key = get_model_key(instance_or_tuple)
    
    if key not in registry.keys():
        raise NotRegistered('Instance not reqistered with Solango')
    
    return registry[key](instance_or_tuple)