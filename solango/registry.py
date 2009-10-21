from UserDict import UserDict

from django.db.models import signals
from django.db.models.base import ModelBase

from solango.solr import get_instance_key

class AlreadyRegistered(Exception):
    pass

class NotRegistered(Exception):
    pass

class DocumentRegistry(UserDict):
    
    def get_document(self, instance):
        
        key = get_instance_key(instance)

        if key not in self.data.keys():
            raise NotRegistered('Instance not reqistered with Solango')
    
        return self.data[key](instance)
        
    def register(self, model=None, search_document=None, document_index=None,
                         connect_signals=True):
        """ Register Models With Solango """
    
        assert model is not None or search_document is not None, \
             "Register needs a Model or a Search Document"
    
        document_key = None
        if model:
            document_key = get_instance_key(model)
        elif search_document and search_document.key:
            document_key = document_key
        else:
            raise AttributeError("Register need a model or search document key")
        
        document = self.get(document_key)
        if document:
            raise AlreadyRegistered('%s has already been registered by search'
                                            % (model or search_document))
        
        #Set Defaults
        if not search_document:
            from solango.solr.documents import SearchDocument
            search_document = SearchDocument
        
        if not document_index:
            from solango.solr.indexes import Index
            document_index = Index()
        
        search_document.set_index(document_index)
        
        self[document_key] = search_document
        
        #Connect Signals
        if connect_signals and model:
            signals.post_save.connect(document_index.post_save, model)
            signals.post_delete.connect(document_index.post_delete, model)
    
documents = DocumentRegistry()