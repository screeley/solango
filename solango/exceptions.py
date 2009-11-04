

class SolangoException(Exception): pass
class SolrException(SolangoException): pass
class SolrUnavailable(SolrException): pass