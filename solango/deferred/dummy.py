
from solango.deferred.base import BaseDeferred
from solango.solr.utils import idict

class Deferred(BaseDeferred):
    
    def __init__(self, *args, **kwargs):
        pass
    
    def create_object(self, instance):
        return idict()
    
    def add(self, method, xml, doc_pk=None, error=None):
        return True

    def list(self):
        return []
