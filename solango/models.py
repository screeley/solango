"""
Solango Models
==============
Django Models for Solango

"""

from django.db import models
from datetime import datetime


DEFERRED_METHODS = (
    (0, "delete"),
    (1, "add"),
    (2, "commit"),
    (3, "optimize",)
)

class DeferredObject(models.Model):
    """
    DeferredObject
    --------------
    Model for the database backed for Deferred Models
    
    ..attribute: method
    
        ADD, DELETE, COMMIT, OPTIMIZE Does the xml document need to be added or
        deleted
    
    ..attribute: doc_pk 
    
        Primary key of the document if one
        
    ..attribute: xml
    
        XML representation of the document Save the XML so we can just add or 
        delete it.
    
    ..attribute: error
    
        If we couldn't send it to solr, why?
        
    ..attribute: action_time
    
        When did we try to do this
    
    """
    method = models.SmallIntegerField(choices=DEFERRED_METHODS)
    doc_pk  = models.CharField(max_length=200, blank=True, null=True)
    xml = models.TextField()
    error = models.TextField(blank=True, null=True)
    action_time = models.DateTimeField(default=datetime.now)
    
    
    def __unicode__(self):
        return u"%s: %s" % (self.method, self.xml[:50])