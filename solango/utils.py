#
# Copyright 2008 Optaros, Inc.
#
import urllib, datetime
from solango import settings

def get_base_url(request, exclude=[]):
    """
    Returns the base URL for request, with any excluded parameters removed.
    This is useful for constructing pagination or filtering URLs.
    """
    ret = request.path
    
    i = ret.find("?")
    
    if i > -1:
        ret = ret[:i + 1]
    else:
        ret += "?"
    
    if len(request.GET):
        
        get = request.GET.copy()
        
        for e in exclude:
            if e in get:
                get.pop(e)
        
        if len(get):
            get_items = [(k,v.encode('utf-8')) for k,v in get.items()]
            ret += urllib.urlencode(get_items) + "&"
   
    return ret

def get_param(request, name, default=""):
    """
    A convenience function for fetching query string parameters.
    """
    params = request.POST or request.GET
    
    if not name in params:
        return default
    
    return str(params[name])

def get_sort_links(request):
    """
    Returns a list of sort links, allowing users to order their results by
    various criteria.
    """
    links = []
    
    sort_criteria = settings.SEARCH_SORT_PARAMS
    
    sort = get_param(request, "sort", "score desc")
    
    base = get_base_url(request, ["sort", "page"])

    for s in sort_criteria:
        
        if s == sort:
            links.append(sort_criteria[s])
            continue
        
        if s:
            href = base + "sort=" + s
        else:
            href = base
        
        links.append({"anchor": sort_criteria[s], "href": href})
        
    return links

def get_facets_links(request, results):
    """
    Returns a list of facet links, allowing users to quickly drill into their
    search results by fields which support faceting.
    """
    (links, link) = ([], {})
    
    for facet in results.facets:
        #links.append(facet.name.title())
        
        base = get_base_url(request, ["page", facet.name])
        
        link = {
            "anchor": "All", "count": None, "level": "0", "href": base
        }
        
        links.append(link)
        
        val = get_param(request, facet.name, None)
        
        previous_level = 0
        for value in facet.values:
            indent = False
            undent = False
            clean = value.value
            if clean != '':
                if clean.find(" ") is not -1:
                    clean = '"%s"' % clean
            
                if previous_level > value.level:
                    undent = True
                elif previous_level < value.level:
                    indent = True
                    
                link = {
                    "anchor": value.name, 
                    "count": value.count, 
                    "level": value.level,
                    "href": base + facet.name + "=" + clean + "",
                    'indent': indent,
                    'undent': undent,
                }
            
                if val == clean:
                    link["active"] = True
            
                links.append(link)
                previous_level = value.level
    
    return links

def get_facet_date_links(request, results):
    """
    Returns a list of facet date links, allowing users to quickly drill into their
    search results by fields which support faceting.
    """
    (links, link) = ([], {})
    
    params = results.header.get('params', None)
    if params is not None:
        date_gap = params.get('facet.date.gap', None)
        
        if date_gap is not None:
            for facet in results.facet_dates:
                
                links.append(facet.name.title())
                
                base = get_base_url(request, ["page", facet.name])
                
                link = {
                    "anchor": "All", "count": None, "level": "0", "href": base
                }
                
                links.append(link)
                
                val = get_param(request, facet.name, None)
                #import ipdb; ipdb.set_trace()    
                for value in facet.values:
                    clean = value.value
                    #if clean.find(" ") is not -1:
                    clean = urllib.quote('[%s TO %s%s]' % (clean, clean, date_gap))
                    
                    date_value = value.name
                    millisecond_start = date_value.rfind('.')
                    if millisecond_start > -1:
                        date_value = date_value[:millisecond_start] + 'Z'
                    date_obj = datetime.datetime.strptime(date_value, "%Y-%m-%dT%H:%M:%SZ")
                    date_format = "%B %d %Y"
                    if 'YEAR' in date_gap:
                        date_format = "%Y"
                    elif 'MONTH' in date_gap:
                        date_format = "%B %Y"
                        
                    date_str = datetime.datetime.strftime(date_obj, date_format)
                    
                        
                    link = {
                        "anchor": date_str, 
                        "count": value.count, "level": value.level,
                        "href": base + facet.name + "=" + clean + ""
                    }
                    if val is not None:
                        if urllib.quote(val) == clean:
                            link["active"] = True
                    
                    links.append(link)
    
    return links


def create_schema_xml(raw=False):
    import solango
    from solango.settings import SOLR_DEFAULT_OPERATOR
    from django.template.loader import render_to_string
    fields = {}
    
    for doc in solango.registry.values():
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

def reindex(batch_size=None):
    from solango.indexing import indexer
    indexer.index_all(batch_size=batch_size)
    