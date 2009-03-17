#
# Copyright 2008 Optaros, Inc.
#

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.generic.create_update import apply_extra_context

from solango import connection
from solango import utils
from solango.paginator import SearchPaginator
from solango.forms import SearchForm

def select(request, form_class=SearchForm, template_name='solango/search.html', 
            extra_context={}):
    """
    Issues a select request to the search server and renders any results.
    The query term is derived from the incoming URL, while additional
    parameters for pagination, faceting, filtering, sorting, etc come
    from the query string.
    """
    if not connection.is_available():
        return HttpResponseRedirect(reverse('solango_search_error'))
    
    params = {}
    facets = []
    paginator = None
    sort_links = []
        
    if request.GET:
        form = form_class(request.GET)
        if form.is_valid():
            # Get all the get params
            params.update(dict(request.GET.items()))
            # Overwrite those with anything you might of changed in the form.
            params.update(form.cleaned_data)
            paginator = SearchPaginator(params, request)
            facets = utils.get_facets_links( request, paginator.results)
            sort_links = utils.get_sort_links(request)
    else:
        form = form_class()
    
    context = RequestContext(request)
    apply_extra_context(extra_context, context)
    
    return render_to_response(template_name, {'paginator': paginator,
                                              'facets' : facets,
                                              'form' : form,
                                              'sort_links' : sort_links }, context)
