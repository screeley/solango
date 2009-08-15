#
# Copyright 2008 Optaros, Inc.
#
from solango.solr import xmlutils
from solango import settings
import urllib
import datetime

class FacetValue(object):
    """
    An abstraction for a unique facet value count, returned from Solr.  This
    object also supports parent and child relationships to other facet values.
    """
    def __init__(self, value, count=0):
        """
        Initialize value and count, resolving name from the value.
        """
        (self.value, self.count) = (value, count)
        (self.parent, self.children, self.level) = (None, [], 0)
        
        n = self.value.rfind(settings.SEARCH_SEPARATOR)
        if n == -1:
            n = 0
        else:
            n += len(settings.SEARCH_SEPARATOR)
        self.name = self.value[n:].title()
        
        
        n = self.name.rfind(settings.FACET_SEPARATOR)
        if n == -1:
            n = 0
        else:
            n += len(settings.FACET_SEPARATOR)
        self.name = self.name[n:].title()
        
    def get_encoded_value(self):
        """
        Returns the url-encoded value for inclusion in a URL.
        """
        clean = self.value
        if " " in clean:
            clean = '"%s"' % clean
        return urllib.quote(clean)
    
class Facet(object):
    """
    Facets are fields upon which Solr may group search results (analogous to a
    SQL "GROUP BY" clause).  Faceting shows users the results of Solr's
    faceting collation in conjunction with a tree-merge strategy implemented
    in this class.
    
    Example:
      You searched for "Obama"
      
      ... search results ...
      
      By Category
        Politics - 6
          Elections - 4
          Senate - 2
      By Theme
        Election 2008 - 10
        Democratic Party - 4
      By Year
        2007 - 5
        2008 - 11
    """
    (name, values) = (None, None)
    
    def get_parent(self, value):
        """
        Returns the best-fit immediate parent for the specified value, or
        None if value does not appear to have a parent.
        """
        n = value.value.rfind(settings.FACET_SEPARATOR)
        
        if n == -1:
            return None
        
        p = value.value[:n]
        
        for v in self.values:
            if v.value == p:
                return v
        
        f = self.create_value(p, 0)
        self.values.append(f)
        
        return f
    
    def add_to_parent(self, parent, child):
        """
        Appends child to parent, recursing up the tree to increment the counts
        for any ancestors.
        """
        child.parent = parent
        parent.children.append(child)
        
        p = parent
        
        while(p):
            p.count += child.count
            p = p.parent
    
    def recurse_children(self, value):
        """
        Appends value and all of its child values to this facet's values list
        using depth-first recursion.  Value levels are also calculated for
        display purposes.
        """
        
        self.values.append(value)
        
        if value.parent:
            value.level = value.parent.level + 1
        
        if value.children:
            value.value += "*"
        
        for c in value.children:
            self.recurse_children(c)
    
    def merge_values(self):
        """
        Merges facet values which appear to be related to each other by
        parent/child relationships, based on the sharing of name prefixes.
        After merging the facets, depth-first recursion of the resulting
        tree is used to produce a linear, sorted list of values.
        """
        values = []
        
        for v in self.values:
            parent = self.get_parent(v)
                    
            if not parent:
                values.append(v)
                continue
            
            self.add_to_parent(parent, v)
        
        self.values = []
        
        for v in values:
            self.recurse_children(v)
    
    def create_value(self, value, count):
        return FacetValue(value, count)
    
    def __init__(self, node):
        """
        Iterate the provided DOM Node, parsing the facet name and any child
        value counts.  Facet values are additionally merged into a tree
        structure based on common name prefixes, and then flattened out again.
        This allows for parent-child relationships and nested value counts.
        See merge_values.
        
        Parses the facet counts into this Result's facets list.
        
        Takes a parsed xml document.
        """
        (self.name, self.values) = (xmlutils.get_attribute(node, "name"), [])
        
        for c in xmlutils.get_child_nodes(node, "int"):
            
            value = xmlutils.get_attribute(c, "name")
            count = xmlutils.get_int(c)
            self.values.append(self.create_value(value, count))
        
        self.merge_values()

class DateFacetValue(FacetValue):
    """
    An abstraction for a unique date facet value count, returned from Solr.
    """
    def __init__(self, value, count, date_gap):
        """
        Initialize value and count, resolving name from the value.
        """
        self.date_gap = date_gap
        
        super(DateFacetValue, self).__init__(value, count)
        
        date_value = self.name
        
        millisecond_start = date_value.rfind('.')
        if millisecond_start > -1:
            date_value = date_value[:millisecond_start] + 'Z'
        date_obj = datetime.datetime.strptime(date_value, "%Y-%m-%dT%H:%M:%SZ")
        
        precision = self.date_gap.lstrip('+-1234567890')
        date_format = settings.SEARCH_FACET_DATE_FORMATS.get(precision, "%B %d %Y")
        
        self.name = datetime.datetime.strftime(date_obj, date_format)
    
    def get_encoded_value(self):
        """
        Returns the url-encoded value for inclusion in a URL.
        """
        clean = self.value
        if " " in clean:
            clean = '"%s"' % clean
        return urllib.quote('[%s TO %s%s]' % (clean, clean, self.date_gap))

class DateFacet(Facet):
    def __init__(self, facet, date_gap):
        self.date_gap = date_gap
        super(DateFacet, self).__init__(facet)
    
    def create_value(self, value, count):
        return DateFacetValue(value, count, self.date_gap)
        
