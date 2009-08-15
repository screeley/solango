#
# Copyright 2008 Optaros, Inc.
#
from django.template import RequestContext, loader
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.views.generic.create_update import apply_extra_context

from solango import connection
from solango import utils
from solango.paginator import SearchPaginator
from solango.forms import SearchForm


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
    def __init__(self, form_class=None, template_name=None, error_redirect=None):
        self.form_class = form_class
        self.template_name = template_name
        if not error_redirect:
            error_redirect = 'solango_search_error'
        self.error_redirect = error_redirect
    
    def __call__(self, request, form_class=None, template_name=None, extra_context={}):
        return self.main(request, form_class, template_name, extra_context={})

    def main(self, request, form_class=None, template_name=None, extra_context={}):
        """
        Main Function of view
        """
        if not self.is_available():
            return HttpResponseRedirect(reverse(self.error_redirect))
        
        form_class = self.get_form(form_class)
        
        params = {}
        facets = []
        sort_links = []
        facet_dates = []
        
        paginator = None
        if request.GET:
            form = form_class(request.GET)
            if form.is_valid():
                # Get all the get params
                params.update(dict(request.GET.items()))
                # Overwrite those with anything you might of changed in the form.
                params.update(form.cleaned_data)
                paginator = SearchPaginator(params, request)
                facets = utils.get_facets_links(request, paginator.results)
                sort_links = utils.get_sort_links(request)
        else:
            form = form_class()
            
        # Get Context
        context = self.get_context(request, paginator, facets, sort_links, form)
        apply_extra_context(extra_context, context)
        template = self.get_template(request, template_name)
        
        #Render Template
        rendered_template = template.render(context)
        return HttpResponse(rendered_template) 
        
    def is_available(self):
        """
        If you don't want Solango to check for a connection first, 
        set this to true.
        """
        return connection.is_available()
    
    
    def get_form(self, form_class):
        """
        If the form_class is passed in user that one, else the default
        """
        if not form_class:
            form_class = self.form_class
        if not form_class:
            form_class = SearchForm
        return form_class
    
    def get_template(self, request, template_name): 
        """ 
        Returns the loaded Template
        """
        if not template_name:
            template_name = self.template_name
        if not template_name:
            template_name = 'solango/search.html'
        return loader.get_template(template_name) 
    
    
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