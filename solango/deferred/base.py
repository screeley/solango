"""
Deferred Base
=============
Handle deferred objects.


from solango.deferred import handler

handler.defer_add(xml)

handler.defer_delete(xml)

handler.deferred_add()

handler.deferred_delete()

handler.commit()

"""
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