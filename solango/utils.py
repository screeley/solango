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
    
    sort_criteria = settings.SEARCH_SORT_PARAMS
    
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
        base_sep = "?" in base and "&" or "?"
        current_val = request.REQUEST.get(facet.name, None)
        current_val_quoted = current_val and urllib.quote(current_val) or None
        
        facets[facet.name] = {
            'name'    : facet.name,
            'base'    : base,
            'links'   : [],
            'current' : current_val
        }
        
        previous_level = 0
        for value in facet.values:
            indent = False
            undent = False
            clean = value.get_encoded_value()
            if clean != '':
                if previous_level > value.level:
                    undent = True
                elif previous_level < value.level:
                    indent = True
                
                facets[facet.name]['links'].append({
                    'anchor' : value.name,
                    'count'  : value.count,
                    'level'  : value.level,
                    'href'   : "%s&%s=%s" % (base, facet.name, clean),
                    'active' : (current_val_quoted == clean)
                })
                previous_level = value.level
    return facets

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
    
