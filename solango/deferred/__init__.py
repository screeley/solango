

from solango import conf

HANDLERS = ("dummy", 
            "database")

def get_handler(name):
    
    if name not in HANDLERS:
        raise AttributeError("DEFERRED_BACKEND must be one of the following" %
                             ",".join(HANDLERS))
    
    module = __import__('solango.deferred.%s' % name, {}, {}, [''])
    
    return getattr(module, 'Deferred')()

defer = get_handler(conf.DEFERRED_BACKEND)