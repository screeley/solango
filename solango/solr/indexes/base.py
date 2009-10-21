from solango import conf
from solango.solr.connection import SearchWrapper

class Index(object):
    """
    Solr Index
    """
    name = "default_index"
    update_url = ""
    select_urls = ()
    
    _connection = None
    
    def __init__(self, name=None, update_url=conf.SEARCH_UPDATE_URL, 
                 select_urls=conf.SEARCH_SELECT_URLS,
                 ping_urls=conf.SEARCH_PING_URLS,):
        
        if name is not None:
            self.name = name
        self.update_url = update_url
        self.select_urls = select_urls
        self.ping_urls = ping_urls
        
    @property
    def connection(self):
        """Lazy Init a Collection """
        if self._connection is None:
            self._connection = SearchWrapper(self.update_url, 
                                             self.select_urls,
                                             self.ping_urls)
        return self._connection
    
    def ping(self):
        return self.connection.is_available()

    def optimize(self):
        return self.connection.optimize()
    
    def add(self, doc):
        return self.connection.add(doc.to_add_xml())
    
    def delete(self, doc):
        return self.connection.delete(doc.to_delete_xml())
    
    def delete_all(self, doc):
        return self.connection.delete_all()
    
    def delete_by_query(self):
        return self.connection.delete_by_query(doc)

    def select(self, *args, **kwargs):
        return self.connection.select(*args, **kwargs)
    
    def post_save(self, **kwargs):
        pass
    
    def post_delete(self, **kwargs):
        pass