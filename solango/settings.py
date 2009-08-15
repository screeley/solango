#
# Copyright 2008 Optaros, Inc.
#

from django.conf import settings

### Indexing implementation. See the supplied implementations in solango.indexing
SOLR_INDEXER = getattr(settings, "SOLR_INDEXER", "solango.indexing.ImmediateIndexer")

### Search-specific settings.

SEARCH_UPDATE_URL = getattr(settings, "SEARCH_UPDATE_URL", "http://localhost:8983/solr/update")
SEARCH_SELECT_URL = getattr(settings, "SEARCH_SELECT_URL", "http://localhost:8983/solr/select")
SEARCH_PING_URLS =  getattr(settings, "SEARCH_PING_URLS", ["http://localhost:8983/solr/admin/ping",])

#### SOLR
SOLR_ROOT = getattr(settings,"SOLR_ROOT", None)
SOLR_SCHEMA_PATH = getattr(settings,"SOLR_SCHEMA_PATH", None)
SOLR_DATA_DIR = getattr(settings,"SOLR_DATA_DIR", None)

### BATCH INDEX SIZE
SOLR_BATCH_INDEX_SIZE = getattr(settings,"SOLR_BATCH_INDEX_SIZE", 10)

#### Default Query Operator
SOLR_DEFAULT_OPERATOR = getattr(settings, "SOLR_DEFAULT_OPERATOR", "OR")

### Default Sorting criteria
SEARCH_SORT_PARAMS = getattr(settings, "SEARCH_SORT_PARAMS", {
        # "field direction": "anchor" The anchor for display purposes
        "score desc": "Relevance" 
})

### Default Facet Settings
SEARCH_FACET_PARAMS =  getattr(settings, "SEARCH_FACET_PARAMS", [
    ("facet", "true"),             # Basic faceting
    ("facet.field", "model"),      # Facet by model
    
    # date faceting
    #("facet.date", "date"),      # Replace date with the name of your solr date field
    #("facet.date.start", "2000-01-01T00:00:00.000Z"),
    #("facet.date.end", "NOW/DAY+1DAY"),
    #("facet.date.gap", "+1YEAR"),
])

### strftime format strings for displaying faceting links.
SEARCH_FACET_DATE_FORMATS = getattr(settings, "SEARCH_FACET_DATE_FORMATS", {
    'DAY': '%e %b %Y',
    'MONTH': '%B %Y',
    'YEAR': '%Y',
})

SEARCH_HL_PARAMS = getattr(settings, "SEARCH_HL_PARAMS" ,[
    ("hl", "true"),      # basic highlighting
    ("hl.fl", "text"),   # What field to highlight
])

# Lucene Special Characters
# + - && || ! ( ) { } [ ] ^ " ~ * ? : \
SEARCH_SEPARATOR = getattr(settings, "SEARCH_SEPARATOR", "__")

FACET_SEPARATOR = getattr(settings, "FACET_SEPARATOR", ";;")

########## LOGGING ##############

# The filename to which the logger will write.
import os
DIRNAME = os.path.abspath(os.path.dirname(__file__))
LOGGING_CONF = getattr(settings, "LOGGING_CONF", os.path.join(DIRNAME,'conf/logging.conf'))
