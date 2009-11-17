"""
Query
=====

This is wrapper around a Solr Query

We need to handle 3 use cases:

    # User generates own q string
    q = "django OR solango"

    # User passes a tuple
    q = (("model", "entry"), ("q", "django"),)
    
    #User Passes us a Dictionary
    q = {"model" : "entry", "q" : "django"}

"""

import urllib
from copy import deepcopy


class Value(object):

    def __init__(self, data=None, prefix=None, default=None, help_text=None):
        self.data = data
        self.prefix=prefix
        self.default=default
        self.help_text=help_text
        self.name = None
        
    def add(self, value):
        self.data = value

    def set(self, value):
        self.data = value

    def __unicode__(self):
        return unicode(self.data)
    
    def __repr__(self):
        return self.__unicode__()

    def __nonzero__(self):
        if self.data:
            return True
        return False
    
    def url(self):
        if not self.data:
            return ""
        
        name = self.name.replace("_", ".")
        if self.prefix:
            name = self.prefix + name
    
        return "%s=%s" % (name, self.data)

class IntegerValue(Value):pass
class BooleanValue(Value):pass
class FloatValue(Value):pass

class MultiValue(Value):

    def __init__(self, data=None, prefix=None, default=None, help_text=None, per_field=False):
        self.data = []
        if data is not None:
            self.data = data
        self.prefix=prefix
        self.default=default
        self.help_text=help_text
        self.name = None
        self.per_field = per_field

    def add(self, value):
        self.data.append(value)

    def set(self, value):
        
        if not isinstance(value, list):
            self.data = [value]
        else:
            self.data = value

    def url(self):
        if not self.data:
            return ""
    
        name = self.name.replace("_", ".")
        if self.prefix:
            name = self.prefix + name
    
        return urllib.urlencode(["%s=%s" % (name, value) for value in self.data])
    

class UniqueMultiValue(Value):

    def __init__(self, data=None, prefix=None, default=None, help_text=None, per_field=False):
        self.prefix=prefix
        self.default=default
        self.help_text=help_text
        self.data = set()
        if data is not None:
            self.data = data
        self.name = None
        self.per_field = per_field

    def add(self, value):
        if not isinstance(value, list) and not isinstance(value, set):
            self.data.update([value])
        else:
            self.data.update(value)

    def set(self, value):
        
        if not isinstance(value, list):
            self.data = set([value])
        else:
            self.data = set(value)

    def url(self):
        if not self.data:
            return ""
        
        name = self.name.replace("_", ".")
        if self.prefix:
            name = self.prefix + name
        
        values = []
        for value in self.data:
            if self.per_field and isinstance(value, (tuple,list)):
                field = value[0]
                field_value = value[1]
                values.append(("f.%s.%s" % (field, name), field_value))
            else:
                values.append((name, value))
        
        return urllib.urlencode(values)
    

    def __unicode__(self):
        return unicode(list(self.data))


class DelimitedMultiValue(UniqueMultiValue):
    
    def url(self):
        if not self.data:
            return ""
    
        name = self.name.replace("_", ".")
        if self.prefix:
            name = self.prefix + name
    
        return urllib.urlencode([(name, ",".join(self.data))])

class UniqueSingleValue(UniqueMultiValue):pass

class QValue(MultiValue):
    
    operator = "AND"
    
    def add(self, key, value=None):
        if value is not None:
            key = "%s:%s" % (key, value)
        
        if isinstance(key, list):
            self.data.extend(key)
        else:
            self.data.append(key)

    def url(self):
        if not self.data:
            return ""
        
        name = self.name.replace("_", ".")
        if self.prefix:
            name = self.prefix + name
        print self.operator
        operator = " %s " % self.operator
        return urllib.urlencode([(name, operator.join(["%s" % value
                          for value in self.data]))])



def get_query_values(attrs):
    data = {}
    
    for name, value in attrs.items():
        if isinstance(value, Value) or name == "facet" or name=="hl":
            value = attrs.pop(name)
            value.name = name
            data[name] = value
    
    return data
    
class QueryMetaClass(type):
    """
    Meta Class
    """
    def __new__(cls, name, bases, attrs):
        attrs['base_data'] = get_query_values(attrs)
        return  super(QueryMetaClass,
                     cls).__new__(cls, name, bases, attrs)

class QueryBase(object):
    
    __metaclass__ = QueryMetaClass

    def __init__(self, initial=[], **kwargs):
        
        self.data = deepcopy(self.base_data)
        
        params = []
        
        if isinstance(initial, (tuple, list)):
            params.extend(list(initial))
        elif isinstance(initial, dict):
            params.extend(initial.items())
        
        params.extend(kwargs.items())
        
        for key, value in params:
            self.add(key, value)
            
    def url(self):
        return "&".join([value.url() for value in self.data.values() if value])
    
    def __nonzero__(self):
        if self.url():
            return True
        return False

    def __setattr__(self, name, value):
        if  not name.startswith("_") and name != "data" \
                                     and self.data.has_key(name):
            self.data[name].set(value)
        else:
            super(QueryBase, self).__setattr__(name, value)
    
    def __getattr__(self, name):
        if name != "data" and self.data.has_key(name):
            return self.data[name]

        return super(QueryBase, self).__getattr__(name)
    

    def __repr__(self):
        return  unicode(self.data)

class Facet(QueryBase):
    """
    Facet
    -----
    Python Object that represents a Solr Facet query.
    """
    query = UniqueMultiValue(prefix="facet.",
                   default="*:*", 
                   help_text="This param allows you to specify an arbitrary"
                   +"query in the Lucene default syntax to generate a facet"
                   + "count.")
    
    field = UniqueMultiValue(prefix="facet.",
                        help_text="This param allows you to specify a field"
                         + "which should be treated as a facet.")
    
    prefix = UniqueMultiValue(prefix="facet.",
                              help_text="Limits the terms on which to facet"
                              + "to those starting with the given string prefix.",
                              per_field=True)
    sort = UniqueMultiValue(prefix="facet.",
                            help_text ="This param determines the ordering of"
                            + "the facet field constraints. true - sort the "
                            + "constraints by count (highest count first. false"
                            + " - to return the constraints sorted in their index order",
                            per_field=True)                       
    
    limit = UniqueMultiValue(prefix="facet.",
                             default=100,
                             help_text="This param indicates an offset into the"
                             + " list of constraints to allow paging.",
                             per_field=True)
    
    offset = UniqueMultiValue(prefix="facet.",
                             default=0,
                             help_text = "This param indicates an offset into"
                             + " the list of constraints to allow paging.",
                             per_field=True)
    
     
    mincount = UniqueMultiValue(prefix="facet.",
                             default=0,
                             help_text = "Indicates the minimum counts for "
                             + "facet fields should be included in the "
                             + "response. ",
                             per_field=True)
    
    
    missing = UniqueMultiValue(prefix="facet.",
                             default=False,
                             help_text = "Set to `True` this param indicates "
                             + "that in addition to the Term based constraints"
                             + " of a facet field, a count of all matching "
                             + " results which have no value for the field "
                             + "should be computed ",
                             per_field=True)
    
    method = UniqueMultiValue(prefix="facet.",
                             default="fc",
                             help_text = "This parameter indicates what type "
                             + "of algorithm/method to use when faceting a "
                             + "field. `enum` Enumerates all terms in a field,"
                             + " `fc` The facet counts are calculated by "
                             + " iterating over documents that match the query",
                             per_field=True)
    
    enum_cache_minDf = UniqueMultiValue(prefix="facet.",
                             default=0,
                             help_text = "This param indicates the minimum "
                             + "document frequency (number of documents "
                             + "matching a term) for which the filterCache "
                             + "should be used when determining the constraint"
                             + " count for that term. This is only used when "
                             + "`facet.method=enum` method of faceting ",
                             per_field=True)
    
    date = UniqueMultiValue(prefix="facet.",
                            help_text="This param allows you to specify names "
                            + "of fields (of type DateField) which should be "
                            + "treated as date facets. ")

    date_start = UniqueMultiValue(prefix="facet.",
                                  help_text= "The lower bound for the first "
                                  + "date range for all Date Faceting on this "
                                  + "field.",
                                  per_field=True)
    
    date_end = UniqueMultiValue(prefix="facet.",
                                  help_text= "The minimum upper bound for the "
                                  + "last date range for all Date Faceting on "
                                  + "this field",
                                  per_field=True)
    
    date_gap = UniqueMultiValue(prefix="facet.",
                                  help_text= "The size of each date range "
                                  + "expressed as an interval to be added "
                                  + "to the lower bound",
                                  per_field=True) 

    date_hardened = UniqueMultiValue(prefix="facet.",
                                default=False,
                                help_text="A Boolean parameter instructing "
                                + "Solr what to do in the event that "
                                + "`facet.date.gap` does not divide evenly "
                                + "between `facet.date.start` and "
                                + "`facet.date.end`.",
                                per_field=True)
                                     
    date_other = UniqueMultiValue(prefix="facet.", default=False,
                    help_text="This param indicates that in addition to the "
                    +" counts for each date range constraint between "
                    +"`facet.date.start` and `facet.date.end`, counts should "
                    +" also be computed for. `before`: all records with field "
                    +" values lower then lower bound of the first range "
                    +" `after`: all records with field values greater then the"
                    +" upper bound of the last range. `between`: all records "
                    +" with field values between the start and end bounds of "
                    +"all ranges. `none`: compute none of this information "
                    +"`all`: shortcut for before, between, and after",
                    per_field=True)

    _facet = False
            
        
    def __setattr__(self, name, value):
        if name.startswith("facet_"):
            name = name[6:]
        if  not name.startswith("_") and name != "data" \
                                     and self.data.has_key(name):
            self.data[name].set(value)
        else:
            super(Facet, self).__setattr__(name, value)
    
    def __getattr__(self, name):
        if name != "data" and self.data.has_key(name):
            return self.data[name]

        return super(Facet, self).__getattr__(name)
    

    def add(self, name, value):
        name = name.replace(".", "_")
        if name.startswith("facet_"):
            name = name[6:]
        
        if name == "facet":
            self._facet = value
        
        else:
            self.data[name].add(value)
    
    def url(self):
        part = "&".join([value.url() for value in self.data.values() if value])
        if part or self._facet is True:
            part = "facet=true&" + part
        return part

class Highlight(QueryBase):
    
    _hl = False
    
    fl = DelimitedMultiValue(prefix="hl.",
                help_text="A comma delimited list of fields to generate "
                + "highlighted snippets for")
    
    snippets = UniqueMultiValue(prefix="hl.", default=1,
                help_text="The maximum number of highlighted snippets to "
                + "generate per field.",
                per_field=True)
    fragsize =  UniqueMultiValue(prefix="hl.", default=100,
                help_text="The size, in characters, of fragments to consider "
                +"for highlighting. ",
                per_field=True)
    
    mergeContiguous = UniqueMultiValue(prefix="hl.", default=False,
                help_text="Collapse contiguous fragments into a single "
                +"fragment.",
                per_field=True)
    
    requireFieldMatch = BooleanValue(prefix="hl.", default=False,
                help_text="If true, then a field will only be highlighted if "
                + "the query matched in this particular field")
    
    maxAnalyzedChars = IntegerValue(prefix="hl.", default=51200,
                help_text = "How many characters into a document to look for "
                +"suitable snippets")
    
    alternateField = UniqueMultiValue(prefix="hl.", default=None,
                help_text="If a snippet cannot be generated (due to no terms "
                + "matching), you can specify a field to use as the "
                + "backup/default summary.",
                per_field=True)
    
    
    formatter = Value(prefix="hl.", default="simple",
                help_text="Specify a formatter for the highlight output.")
    
    simple_pre = Value(prefix="hl.", default="<em>",
                help_text="The text which appears before a highlighted term")
    
    simple_post = Value(prefix="hl.", default="</em>",
                help_text="The text which appears after a highlighted term")
    
    fragmenter = UniqueMultiValue(prefix="hl.", default="gap",
                help_text="Specify a text snippet generator for highlighted" 
                + " text. The standard fragmenter is gap, Another option is "
                + "regex, which tries to create fragments that `look like` a "
                + "certain regular expression. ",
                per_field=True)
    
    usePhraseHighlighter = BooleanValue(prefix="hl.", default=False,
                help_text="Use SpanScorer to highlight phrase terms only when "
                + "they appear within the query phrase in the document.")
    
    highlightMultiTerm = BooleanValue(prefix="hl.", default=False,
                help_text="If the SpanScorer is also being used, enables "
                + "highlighting for range/wildcard/fuzzy/prefix queries.")
    
    
    regex_slop = FloatValue(prefix="hl.", default=0.6,
                help_text="Factor by which the regex fragmenter can stray from"
                + " the ideal fragment size (given by hl.fragsize) to "
                + "accommodate the regular expression.")
    
    regex_pattern = Value(prefix="hl.", default=None,
                help_text="The regular expression for fragmenting. This could "
                + "be used to extract sentences (see example solrconfig.xml)")
    
    regex_maxAnalyzedChars = IntegerValue(prefix="hl.", default=10000,
                help_text="Only analyze this many characters from a field when"
                + " using the regex fragmenter")

    def __setattr__(self, name, value):
        if name.startswith("hl_"):
            name = name[3:]
        if  not name.startswith("_") and name != "data" \
                                     and self.data.has_key(name):
            self.data[name].set(value)
        else:
            super(Highlight, self).__setattr__(name, value)
    
    def add(self, name, value):
        name = name.replace(".", "_")
        if name.startswith("hl_"):
            name = name[3:]
        
        if name == "hl":
            self._hl = value
        
        else:
            self.data[name].add(value)
    
    def url(self):
        part = "&".join([value.url() for value in self.data.values() if value])
        if part:
            part = "hl=true&" + part
        elif self._hl is True:
            part = "hl=true"
        return part

class Query(QueryBase):
    """
    Query
    -----
    Object for building solr queries
    
    ..attribute qt:
        
        If a request uses the /select URL, and no SolrRequestHandler has been
        configured with /select as its name, then Solr uses the qt (query type)
        parameter to determine which Query Handler should be used to process
        the request. Valid values are any of the names specified by 
        <requestHandler ... /> declarations in solrconfig.xml
        
        The default value is "standard". 
    
    ..attribute wt:
        
        The wt (writer type) parameter is used by Solr to determine which
        QueryResponseWriter should be used to process the request. Valid values
        are any of the names specified by <queryResponseWriter... /> 
        declarations in solrconfig.xml

        The default value is "json". 
    
    ..attribute echoHandler:
    
        If the echoHandler parameter is true, Solr places the name of the
        handle used in the response to the client for debugging purposes.
    
    ..attribute echoParams:
    
    The echoParams parameter tells Solr what kinds of Request parameters should be included in the response for debugging purposes, legal values include:

    * none - don't include any request parameters for debugging
    * explicit - include the parameters explicitly specified by the client in the request
    * all - include all parameters involved in this request, either specified explicitly by the client, or implicit because of the request handler configuration. 
    
    """
    
    #Common Query Params: http://wiki.apache.org/solr/CommonQueryParameters
    q = QValue(default="*:*",
               help_text="This is the only mandatory query parameter. Search"
               + " string used by solr")
    sort = UniqueMultiValue()
    start =  Value()
    rows = Value()
    fq = UniqueMultiValue()
    fl = DelimitedMultiValue()
    debugQuery = Value()
    explainOther = Value()
    defType = Value()
    timeAllowed = Value()
    omitHeader = Value()
    wt = Value(data="json")
        
    #http://wiki.apache.org/solr/DisMaxRequestHandler
    q_alt = QValue()
    qf = UniqueMultiValue()
    mm = Value()
    pf = UniqueMultiValue()
    ps = Value()
    tie = Value()
    bq = QValue()
    bf = UniqueMultiValue()
    qt = Value()
    df = Value()
    
    facet = Facet()
    hl = Highlight()

    def __init__(self, initial=[], **kwargs):
        self.data = deepcopy(self.base_data)
        
        params = []
        
        if isinstance(initial, basestring):
            params.append(("q", initial))
        elif isinstance(initial, (tuple, list)):
            params.extend(list(initial))
        elif isinstance(initial, dict):
            params.extend(initial.items())
        
        params.extend(kwargs.items())
        
        for key, value in params:
            #per field attrs: `f.cat.facet.missing=true`
            if key.startswith("f."):
                parts = key.split(".")
                name = parts[1]
                key = ".".join(parts[2:])
                value = (name, value)
            
            if key.startswith("facet"):
                self.facet.add(key, value)
            elif key.startswith("hl"):
                self.hl.add(key, value)
            else:
                self.add(key, value)
                

    def __setattr__(self, name, value):
        if not name.startswith("_") and name != "data" \
                                    and self.data.has_key(name):
            self.data[name].set(value)
        else:
            super(Query, self).__setattr__(name, value)
    
    def __getattr__(self, name):
        if not name.startswith("_") and name != "data" \
                                    and self.data.has_key(name):
            return self.data[name]

        return super(Query, self).__getattr__(name)
    
    def add(self, key, value):
        if key.startswith("facet"):
            self.facet.add(key, value)
        elif key.startswith("hl"):
            self.hl.add(key, value)
        else:
            if self.data.has_key(key):
                self.data[key].add(value)
            else:
                self.data["q"].add(key, value)
    
    def url(self):
        return "?%s" % "&".join([value.url() for value in self.data.values() if value])
    
    def merge(self, query):
        #will merge a another query in with this one.
        assert isinstance(query, Query), "Merge only accepts Query element"
        
        for value in query.data.values():
            self.add(value.name, value.data)
        