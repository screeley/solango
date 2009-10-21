"""
Deferred Cache
=============
Handle deferred objects.

"""

from django.core.cache import cache

class Deferred(object):

    add_cache_key = "solango_deferred_cache_add"
    delete_cache_key = "solango_deferred_cache_delete"

    def defer_add(self, xml):
        
        xml_list = cache.get(self.add_cache_key)
        if xml_list:
            xml_list.append(xml)
        else:
            xml_list = [xml]

        cache.set(self.add_cache_key, xml_list)
    
    def defer_delete(self, xml):
        
        xml_list = cache.get(self.delete_cache_key)
        if xml_list:
            xml_list.append(xml)
        else:
            xml_list = [xml]

        cache.set(self.delete_cache_key, xml_list)
    
    def deferred_add(self):
        xml_list = cache.get(self.add_cache_key)
        if xml_list:
            return xml_list
        
        return []
    
    def deferred_delete(self):
        xml_list = cache.get(self.delete_cache_key)
        if xml_list:
            return xml_list
        
        return []
    
    def commit(self):
        pass