#
# Copyright 2008 Optaros, Inc.
#
import urllib, datetime
from solango import conf
import threading

def get_base_url(request, exclude=[]):
    """
    Returns the base URL for request, with any excluded parameters removed.
    This is useful for constructing pagination or filtering URLs.
    """
    if request.GET:
        get = [(k,v.encode('utf-8')) for k,v in request.GET.items() if k not in exclude]
        return "%s?%s" % (request.path, urllib.urlencode(get))
    else:
        return request.path

def get_sort_links(request):
    """
    Returns a list of sort links, allowing users to order their results by
    various criteria.
    """
    links = []
    
    sort_criteria = conf.SEARCH_SORT_PARAMS
    
    sort = request.REQUEST.get("sort", "score desc")
    
    base = get_base_url(request, ["sort", "page"])

    for s in sort_criteria.keys():
        current = s == sort
        href = base
        if s:
            href += "?" in href and "&" or "?"
            href += "sort=" + s
        
        links.append({"anchor": sort_criteria[s], "href": href})
        
    return links

def get_facets_links(request, results):
    """
    Returns a dictionary of facet links, allowing users to quickly drill 
    into their search results by fields which support faceting.
    """
    facets = {}
    for facet in results.facets:
        base = get_base_url(request, ["page", facet.name])
        current_val = request.REQUEST.get(facet.name, None)
        current_val_quoted = current_val and urllib.quote(current_val) or None
        
        facets[facet.name] = {
            'name'    : facet.name,
            'base'    : base,
            'links'   : [],
            'current' : current_val is None
        }
        
        for value in facet.values:
            clean = value.get_encoded_value()
            if clean != '':                
                facets[facet.name]['links'].append({
                    'anchor' : value.name,
                    'count'  : value.count,
                    'level'  : value.level,
                    'href'   : "%s&%s=%s" % (base, facet.name, clean),
                    'active' : (current_val_quoted == clean)
                })
    return facets

def create_schema_xml(raw=False):
    import solango
    from solango.conf import SOLR_DEFAULT_OPERATOR
    from django.template.loader import render_to_string
    fields = {}
    
    for doc in solango.documents.values():
        fields.update(doc.base_fields)
    
    doc, copy_doc = "", ""
    copy_fields = []
    for field in fields.values():
        if not field.dynamic:
            doc += field._config() + '\n'
            if field.copy:
                copy_fields.append(field)
    
    for copy_field in copy_fields:
        copy_doc += copy_field._config_copy() + '\n'
    
    if raw:
        print '########## FIELDS ########### \n'
        print doc
        print '######## COPY FIELDS ######## \n'
        print copy_doc
    else:
        return render_to_string('solango/schema.xml', {'fields': doc, "copy_fields"  : copy_doc, 'default_operator': SOLR_DEFAULT_OPERATOR})


def reindex(batch_size=50, document_key=None):
    import solango
    
    if document_key:
        document = solango.documents.get(document_key)
        model = solango.solr.get_model_from_key(document_key)
        document.index.reindex(model, document, batch_size=batch_size)
    else:
        for model_key, document in solango.documents.items():
            model = solango.solr.get_model_from_key(model_key)
            document.index.reindex(model, document, batch_size=batch_size)


class ReIndexThread(threading.Thread):
    
    def __init__(self, qs, batch_size, index, commit=False):
        self.qs = qs
        self.batch_size = batch_size
        self.index = index
        self.commit = commit
        threading.Thread.__init__(self)
        
    def run(self):
        self.index().reindex_qs(self.qs,self.batch_size, self.commit)
        print "DONE"

   
def quick_reindex(qs, batch_size=50, threads=4):
    import solango
    solango.autodiscover()
    count = qs.count()
    
    batch = count/threads
    
    for i in range(threads):
        start = i*batch
        stop = (i+1)*batch
        
        if i is (threads-1):
            stop = count

        #We only want one thread to do the committing.
        commit = False
        if i == 1:
            commit = True

        t = ReIndexThread(qs[start:stop], batch_size, solango.Index, commit)
        t.start()

def test_reindex():
    import solango
    solango.autodiscover()
    for model_key, document in solango.documents.items():
        print "Model ", model_key
        print "Document ", document
        model = solango.solr.get_model_from_key(model_key)
        print "Count ", model._default_manager.count()
        now = datetime.datetime.now()
        for instance in model._default_manager.iterator():
            doc = document(instance)
            doc.to_add_xml()
            
        elapsed = datetime.datetime.now() - now
        print "Elapsed Seconds ", elapsed.seconds