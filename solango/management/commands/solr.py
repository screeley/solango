#
# Copyright 2008 Optaros, Inc.
#

from django.core.management.base import BaseCommand, CommandError, NoArgsCommand
from optparse import make_option
import os
import shutil
import subprocess

class Command(NoArgsCommand):
    option_list = BaseCommand.option_list + (
        make_option('--flush', dest='flush_solr', action='store_true', default=False,
            help='Will remove the data directory from Solr.'),                      
        make_option('--reindex', dest='index_solr', action='store_true', default=False,
            help='Will reindex Solr from the registry.'),
        make_option('--batch-size', dest='index_batch_size', default=False,
            help='Used with --reindex. Sets solr index batch size.'),
        make_option('--schema', dest='solr_schema', action='store_true', default=False,
            help='Will create the schema.xml in SOLR_SCHEMA_PATH or in the --path.'),
        make_option('--path', dest='schema_path', default=False,
            help='Tells Solango where to create config file.'),
        make_option('--fields', dest='solr_fields', action='store_true', default=False,
            help='Prints out the fields the schema.xml will create'),
        make_option('--start', dest='start_solr', action='store_true', default=False,
            help='Start solr running java -jar start.jar'),
        make_option('--index-queued', dest='index_queued', action='store_true', default=False,
            help='Indexes all the documents in the index queue table, and truncates the table.'),
    )
    args = ''

    def handle(self, *args, **options):
        if args:
            raise CommandError("Command doesn't accept any arguments")
        return self.handle_noargs(**options)

    def handle_noargs(self, **options):
        index_solr = options.get('index_solr')
        index_batch_size = options.get('index_batch_size')
        schema = options.get('solr_schema')
        schema_path = options.get('schema_path')
        flush_solr =options.get('flush_solr')
        solr_fields =options.get('solr_fields')
        start_solr = options.get('start_solr')
        index_queued = options.get('index_queued')
         
        from solango import settings
        
        #### SOLR
        SOLR_SCHEMA_PATH = getattr(settings, 'SOLR_SCHEMA_PATH', None)
        SOLR_DATA_DIR = getattr(settings, 'SOLR_DATA_DIR', None)
        SOLR_ROOT = getattr(settings, 'SOLR_ROOT', None)
        
        if solr_fields:
            from solango.utils import create_schema_xml
            create_schema_xml(True)
        
        if schema:
            #Get the Path
            path = None
            if schema_path:
                path = schema_path
            elif SOLR_SCHEMA_PATH:
                path = SOLR_SCHEMA_PATH
            else:
                raise CommandError("Need to specify either a SOLR_SCHEMA_PATH in settings.py or use --path")
            #Make sure the path exists
            if not os.path.exists(path):
                raise CommandError("Path does not exist: %s" % path)
            
            if not os.path.isfile(path):
                path = os.path.join(path, 'schema.xml')
            
            from solango.utils import create_schema_xml
            f = open(path, 'w')
            f.write(create_schema_xml())
            f.close()
            print """
Successfully created schema.xml in/at: %s

******************************************************************************
* Warning : You must restart Solr in order for these changes to take affect. *
******************************************************************************
                """ % path
        
        if flush_solr:
            import solango
            if solango.connection.is_available():
                raise CommandError("Flush has a tendency to fail if Solr is running. Please shut it down first.")
            
            if SOLR_DATA_DIR:
                if not os.path.exists(SOLR_DATA_DIR):
                    raise CommandError("Solr Data Directory has already been deleted or doesn't exist: %s" % SOLR_DATA_DIR)
                else:
                    answer = raw_input('Do you wish to delete %s: [y/N] ' % SOLR_DATA_DIR)
                    if answer == 'y' or answer == 'Y':
                        shutil.rmtree(SOLR_DATA_DIR)
                        print 'Removed %s' % SOLR_DATA_DIR
                    else:
                        print 'Did not remove %s' % SOLR_DATA_DIR
            else:
                raise CommandError("Path does not exist: %s" % path)
        
        if index_solr:
            import solango
            if not solango.connection.is_available():
                raise CommandError("Solr connection is not available")
            
            from solango.utils import reindex
            if not index_batch_size:
                index_batch_size = getattr(settings,"SOLR_BATCH_INDEX_SIZE")

            try:
                # Throws value errors.
                index_batch_size = int(index_batch_size)
                print "Starting to reindex Solr"
                reindex(batch_size = index_batch_size)
                print "Finished the reindex of Solr"
            except ValueError, e:
                raise CommandError("ERROR: Invalid --batch-size agrument ( %s ). exception: %s" % (str(index_batch_size), str(e)))
            
        if start_solr:
            # Make sure the `SOLR_ROOT` and `start.jar` exist.
            if not SOLR_ROOT:
                raise CommandError("SOLR_ROOT is not specified")
            start_jar_path = os.path.join(SOLR_ROOT, 'start.jar')
            if not os.path.exists(start_jar_path):
                raise CommandError("No Solr start.jar found at %s" % start_jar_path)
            
            # Start Solr subprocess
            print "Starting Solr process. CTL-C to exit."
            os.chdir(SOLR_ROOT)
            try:
                subprocess.call(["java", "-jar", "start.jar"])
            except KeyboardInterrupt:
                # Throws nasty errors if we don't catch the keyboard interrupt.
                pass
            print "Solr process has been interrupted"
            
        if index_queued:
            from solango.indexing import indexer
            indexer.index_queued()
