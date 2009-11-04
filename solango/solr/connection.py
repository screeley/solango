#
# Copyright 2008 Optaros, Inc.
#

from datetime import datetime, timedelta
import urllib2

from solango import conf
from solango.log import logger
from solango.solr import results
from solango.solr.query import Query
from solango.exceptions import SolrUnavailable, SolrException

(DELETE, ADD) = (0,1)

class SearchWrapper(object):
    """
    This class is the entry point for all search-bound actions, including
    adding (indexing), deleting, and selecting (searching).
    """
    
    available = False
    hearbeat = None
    
    def __init__(self, update_url, select_url, ping_urls):
        """
        Resolves configuration and instantiates a Log for this object.
        """
        self.update_url = update_url
        self.select_url = select_url
        self.ping_urls = ping_urls
        self.heartbeat = datetime(1970, 01, 01)
    
    def is_available(self):
        """
        Returns True if the search system appears to be available and in good
        health, False otherwise.  A ping is periodically sent to the search
        server to query its availability.
        """
        (now, delta) = (datetime.now(), timedelta(0, 300))
        
        if now - self.heartbeat > delta:
            try:
                for url in self.ping_urls:
                    res = urllib2.urlopen(url).read()
            except StandardError:
                self.available = False
            else:
                self.available = True
            
        return self.available
    
    
    
    def _update_request(self, method, xml):
        """
        Issues update requests
        """
        
        if not xml:
            raise SolrException("No XML to Add")
        
        if not self.is_available():
            return results.ErrorResults(method, self.update_url, xml, "Solr Unavailable")
        
        xml = xml.encode("utf-8", "replace")
        
        request = urllib2.Request(self.update_url, xml)
        request.add_header("Content-type", "text/xml; charset=utf-8")
        
        response = None
        try:
            response = urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            return results.ErrorResults(method, self.update_url, xml, str(e), e.code)
        except urllib2.URLError, e: 
            return results.ErrorResults(method, self.update_url, xml, str(e))
        
        return results.UpdateResults(response.read())
    
    def _select_request(self, url):
        """
        Issues update requests
        """
        
        if not self.is_available():
            raise SolrUnavailable("Unable to add documents to Solr")
        
        request = urllib2.Request(url)
        request.add_header("Content-type", "application/json; charset=utf-8")

        response = None
        try:
            response = urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            return results.SelectErrorResults(url, str(e), e.code)
        except  urllib2.URLError, e:
            return results.SelectErrorResults(url, str(e))
        
        return results.SelectResults(url, response.read())

       
    def add(self, xml, commit=True):
        """
        Adds the specified list of objects to the search index.  Returns a
        two-element List of UpdateResults; the first element corresponds to
        the add operation, the second to the subsequent commit operation.
        """
        
        if xml:
            xml = "\n<add>\n" + xml + "</add>\n"
        
        results=[]
        
        results.append(self._update_request("add", xml))
        
        if commit:
            results.append(self.commit())
        
        return results
    
    def delete_all(self, commit=True):
        return self.delete_by_query(q='*:*', commit=commit)

    def delete_by_query(self, q, commit=True):

        res = self.update(
            unicode("\n<delete><query>%s</query></delete>\n" % q, "utf-8")
        )
        if commit:
            ret = [results.UpdateResults(res), self.commit()]
        else:
            ret = [results.UpdateResults(res),]
        return ret

    def delete(self, xml, commit=True):
        """
        Deletes the specified list of objects from the search index.  Returns
        a two-element List of UpdateResults; the first element corresponds to
        the delete operation, the second to the subsequent commit operation.
        """
        
        if xml:
            xml = "\n<delete>\n" + xml + "</delete>\n"
                
        results=[]
        
        results.append(self._update_request("delete", xml))
        
        if commit:
            results.append(self.commit())
        
        return results
    
    def commit(self):
        """
        Commits any pending changes to the search index.  Returns an
        UpdateResults instance.
        """
        return self._update_request("commit", 
                                    unicode("\n<commit/>\n", "utf-8"))
    
    def optimize(self):
        """
        Optimizes the search index.  Returns an UpdateResults instance.
        """
        return self._update_request("optimize", 
                                    unicode("\n<optimize/>\n", "utf-8"))
    
    def update(self, xml):
        """
        Submits the specified Unicode content to Solr's update interface (POST).
        """
        return self._update_request("update", xml)
    
    def select(self, initial=None, **kwargs):
        """
        Submits the specified query to Solr's select interface (GET).
        """
        
        if initial and isinstance(initial, Query):
            query= initial
        else:
            query = Query(initial, **kwargs)

        request_url = self.select_url + query.url()
        return self._select_request(request_url)
