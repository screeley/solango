"""
Deferred Base
=============
Handle deferred objects.


from solango.deferred import defer

defer.add(method, xml, doc_pk, error)

"""

class BaseDeferred(object):

    def create_object(self, instance):
        raise NotImplementedError

    def add(self, method, xml, doc_pk=None, error=None):
        raise NotImplementedError

    def list(self):
        raise NotImplementedError