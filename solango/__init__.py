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

class AlreadyRegistered(Exception):
    pass

class NotRegistered(Exception):
    pass

connection = SearchWrapper()
SearchDocument = SearchDocument
        
def post_save(sender, instance, created, *args, **kwargs):
    """
    Apply any necessary pre-save moderation steps to new
    comments.
    
    """
    key = get_model_key(instance)
    
    if key not in registry.keys():
        return None
    
    document = registry[key](instance)

    # Could be a pain, but only way to make sure the index is updated. 
    if document.is_indexable(instance):
        #Note adding and updating a document in solr uses the same command
        connection.add([document])
    else:
        connection.delete([document])


def post_delete( sender, instance, *args, **kwargs):
    """
    Apply any necessary post-save moderation steps to new
    comments.
    
    """
    key = get_model_key(instance)
    
    if key not in registry.keys():
        return None
    
    document = registry[key](instance)
    connection.delete([document,]) 

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
            signals.post_save.connect(post_save, model)
            signals.post_delete.connect(post_delete, model)

for a in django_settings.INSTALLED_APPS:
    try:
        """
        This will call all the fun things in the search documents
        """
        module = __import__(a + '.search', {}, {}, [''])
    except ImportError, e:
        pass

def get_document(instance):
    """
    Helper to get document from instance
    """
    key = get_model_key(instance)
    
    if key not in registry.keys():
        raise NotRegistered('Instance not reqistered with Solango')
    
    return registry[key](instance)