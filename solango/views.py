#
# Copyright 2008 Optaros, Inc.
#
from copy import deepcopy

from django.template import RequestContext, loader
from django.http import HttpResponseServerError, HttpResponse
from django.core.urlresolvers import reverse
from django.views.generic.create_update import apply_extra_context
from django.shortcuts import render_to_response

import solango
from solango import utils
from solango.paginator import SearchPaginator
from solango.forms import SearchForm
from solango.deferred import defer

class SearchView(object):
    """
    Class based view object. Makes it easier to create custom views
    while keeping the structure of the orginal call.
    
    Issues a select request to the search server and renders any results.
    The query term is derived from the incoming URL, while additional
    parameters for pagination, faceting, filtering, sorting, etc come
    from the query string.
    
    Based on the upcoming django views. by jkocherhans
        http://code.djangoproject.com/attachment/ticket/6735/new-generic-views.3.diff
    """
    _index = None
    
    def __init__(self, form_class=None, template=None):
        self.form_class = form_class
        self.template = template
        self.results = None
    
    @property
    def index(self):
        """Lazy get Index"""
        if self._index is None:
            self._index = solango.Index()
        return self._index
    
    def __call__(self, request, form_class=None, template=None, extra_context={}):
        return self.main(request, form_class, template, extra_context={})


    def select(self, params):
        self.results = self.index.select(params)
        print self.results.url
        return self.results

    def main(self, request, form_class=None, template=None, extra_context={}):
        """
        Main Function of view
        """
                
        form_class = self.get_form(form_class)
        
        params = []
        facets = []
        sort_links = []
        facet_dates = []
        
        paginator = None
        if request.GET:
            form = form_class(request.GET)
            if form.is_valid():
                # Get all the get params
                
                params = deepcopy(request.GET)
                
                page = int(params.pop("page", [1])[0])
                per_page = int(params.pop("per_page", [25])[0])
                
                params.update(form.cleaned_data)
                
                query = self.index.query(params.items())
                query.start = (page-1)*per_page
                query.rows = per_page

                results = self.select(query)
                
                paginator = SearchPaginator(results, request, page, per_page)
                
                facets = utils.get_facets_links(request, paginator.results)
                sort_links = utils.get_sort_links(request)
        else:
            form = form_class()
            
        # Get Context
        context = self.get_context(request, paginator, facets, sort_links, form)
        apply_extra_context(extra_context, context)
        template = self.get_template(request, template)
        
        #Render Template
        rendered_template = template.render(context)
        return HttpResponse(rendered_template) 
        
    def is_available(self):
        """
        If you don't want Solango to check for a connection first, 
        set this to true.
        """
        return Index().is_available()
    
    
    def get_form(self, form_class):
        """
        If the form_class is passed in user that one, else the default
        """
        if not form_class:
            form_class = self.form_class
        if not form_class:
            form_class = SearchForm
        return form_class
    
    def get_template(self, request, template): 
        """ 
        Returns the loaded Template
        """
        if not template:
            template = self.template
        if not template:
            template = 'solango/search.html'
        return loader.get_template(template) 
    
    
    def get_context(self, request, paginator, facets, sort_links, form): 
        """ 
        Returns the Context
        """ 
        return RequestContext(request, {'paginator': paginator,
                                        'facets' : facets,
                                        'form' : form,
                                        'sort_links' : sort_links }) 
    
# View.
select = SearchView()


def deferred(request):
    
    return render_to_response("solango/deferred.html", 
                              {"objects" : defer.list()}, 
                                RequestContext(request))