
import solango
from solango.solr import get_model_key, get_model_from_key

class BaseIndexer(object):
    def _get_all(self):
        for model_key, document in solango.registry.items():
            model = get_model_from_key(model_key)
            for instance in model.objects.all():
                yield instance
        
    def index_all(self, batch_size=None):
        """
        Reindexes all of the models registered to solango
        """
        self._index_multiple(self._get_all(), batch_size=batch_size)
        
    def index_queued(self, batch_size=None):
        raise NotImplementedError, "%s doesn't have a queue! Maybe settings.SOLR_INDEXER is incorrect?" % self.__class__.__name__
    
    def post_save(self, sender, instance, created, *args, **kwargs):
        """
        Update the search index for the model instance.
        This may either add or delete the document from the search index,
        depending on the result of document.is_indexable(instance)
        """
        self.index_instance(instance)
        
    def post_delete(self, sender, instance, *args, **kwargs):
        self.index_instance(instance)
    
    def index_instance(self, instance):
        raise NotImplementedError
    
    def _index_multiple(self, instances, batch_size=None):
        """
        Indexes multiple items immediately
        """
        import solango
        from solango.solr import get_model_from_key
        
        to_index = []
        to_delete = []
        
        if batch_size is None:
            batch_size = getattr(solango.settings,"SOLR_BATCH_INDEX_SIZE", 10)
        
        for instance in instances:
            doc = solango.get_document(instance)
            if doc.is_deleted():
                to_delete.append(doc)
            else:
                if isinstance(instance, (list, tuple)):
                    model = get_model_from_key(instance[0])
                    instance = model.objects.get(pk=instance[1])
                if doc.is_indexable(instance):
                    to_index.append(doc)
                else:
                    to_delete.append(doc)
            
            if (len(to_index) >= batch_size):
                solango.connection.add(to_index)
                to_index = []
            
            if (len(to_delete) >= batch_size):
                solango.connection.delete(to_delete)
                to_delete = []
                
                
        if (len(to_index) > 0):
            solango.connection.add(to_index)
        
        if (len(to_delete) > 0):
            solango.connection.delete(to_delete)

        # optimize() will also commit()
        solango.connection.optimize()
    
class ImmediateIndexer(BaseIndexer):
    def index_instance(self, instance):
        self._index_multiple([instance])

class QueuedIndexer(BaseIndexer):
    def index_instance(self, instance):
        key = get_model_key(instance)
        self.add(instance)
    
    def add(self, instance):
        raise NotImplementedError

class DBQueuedIndexer(QueuedIndexer):
    def __init__(self, *args, **kwargs):
        super(DBQueuedIndexer, self).__init__(*args, **kwargs)
        self._max_indexed_id = None
    
    def add(self, instance):
        from solango.models import IndexQueue
        
        model_key = get_model_key(instance)
        IndexQueue.objects.create(model_key=model_key, instance_id=instance.pk)

    def _get_queued(self):
        """
        A generator that yields some (model_key, instance_id) tuples which were 
        previously queued for indexing.
        
        These may no longer exist, if they have been deleted before the indexer
        runs.
        
        This function does not remove anything from the queue.
        """
        from solango.models import IndexQueue
        
        qs = IndexQueue.objects.order_by('-pk')[:1]
        if qs:
            self._max_indexed_id = qs[0].pk
        else:
            self._max_indexed_id = None
            return
        queryset = IndexQueue.objects.filter(id__lte=self._max_indexed_id).order_by('id')
        
        # TODO: should we do SELECT FOR UPDATE here?
        # If cron jobs run too close together, there may be concurrency issues...
        # 
        # QuerySet.for_update() --> http://code.djangoproject.com/ticket/2705
        # Until for_update() is included in Django, make sure your indexing runs 
        # don't happen in parallel!
        ### queryset = queryset.for_update()
        
        batch_size = solango.settings.SOLR_BATCH_INDEX_SIZE
        i = 0
        done = {}
        while True:
            qs = queryset[i:i+batch_size]
            if not qs:
                break
            for iq in qs:
                # Avoid indexing the same thing twice
                if iq.model_key not in done.keys():
                    done[iq.model_key] = set()
                if iq.instance_id not in done[iq.model_key]:
                    done[iq.model_key].add(iq.instance_id)
                    yield iq.model_key, iq.instance_id
            i += batch_size
    
    def index_queued(self, batch_size=None):
        """
        Indexes all queued documents and removes the documents from the queue.
        """
        from solango.models import IndexQueue
        
        self._index_multiple(self._get_queued(), batch_size=batch_size)
        if self._max_indexed_id:
            IndexQueue.objects.filter(pk__lte=self._max_indexed_id).delete()

def _create_indexer():
    typ = solango.settings.SOLR_INDEXER.rsplit('.', 1)
    module = __import__(typ[0], {}, {}, [''])
    cls = getattr(module, typ[1])
    return cls()

indexer = _create_indexer()