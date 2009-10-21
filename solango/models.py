"""
Solango Models
==============
Django Models for Solango

"""

from django.db import models

DEFERRED_METHODS = (
    (0, "Delete"),
    (1, "Add"),
)

class DeferredObject(models.Model):
    """
    DeferredObject
    --------------
    Model for the database backed for Deferred Models
    
    ..attribute method: ADD or DELETE
        Does the xml document need to be added or deleted
    
    ..attribute doc_pk: Primary key of the document.
        Used to make sure we don't have dups.
        
    ..attribute xml: XML representation of the document
        Save the XML so we can just add or delet it.
    
    """
    method = models.SmallIntegerField(choices=DEFERRED_METHODS)
    doc_pk  = models.CharField(max_length=200)
    xml = models.TextField()
    
    def __unicode__(self):
        return u"%s: %s" % (self.method, xml[:50])