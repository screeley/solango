"""
Deferred Database
=============
Handle deferred objects.

"""

from solango.solr.utils import idict
from solango.deferred.base import BaseDeferred
from solango.models import DeferredObject, DEFERRED_METHODS

class Deferred(object):
    
    def create_object(self, instance):
        obj = idict()
        for field in ["method", "xml", "doc_pk", "error"]:
            obj[field] = getattr(instance, field)        
        return obj
        
    def add(self, method, xml, doc_pk=None, error=None):
        
        method_int = None
        for meth in DEFERRED_METHODS:
            if meth[1] == method:
                method_int = meth[0]
        
        if method_int is None:
            raise ValueError("unknown method: %s" % method)
        
        df = DeferredObject.objects.create(method=method_int, xml=xml, 
                                      doc_pk=doc_pk, error=error)

        return self.create_object(df)

    def list(self):
        return DeferredObject.objects.all()