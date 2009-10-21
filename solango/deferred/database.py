"""
Deferred Database
=============
Handle deferred objects.

"""

from solango.models import DeferredObject

class Deferred(object):

    def defer_add(self, xml):
        pass

    def defer_delete(self, xml):
        pass

    def deferred_add(self):
        return []
    
    def deferred_delete(self):
        return []

    def commit(self):
        pass