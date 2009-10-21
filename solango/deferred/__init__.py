

from solango.conf import DEFERRED_BACKEND

HANDLERS = ("base", "cache", "database", "mongodb",)

def get_handler(name):
    
    if name not in HANDLERS:
        raise AttributeError("DEFERRED_BACKEND must be one of the following" %
                             ",".join(HANDLERS))
    
    module = __import__('solango.deferred.%s' % name, {}, {}, [''])
    
    return getattr(module, 'Deferred')()

handler = get_cache(DEFERRED_BACKEND)