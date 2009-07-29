from django.db import models

class IndexQueue(models.Model):
    "The indexing queue used by solango.indexing.DBQueuedIndexer for delayed indexing"
    model_key = models.CharField(max_length=255, null=False)
    instance_id = models.IntegerField(null=False)
