from django.core.management.commands.dumpdata import Command as DumpData

from applications import add_db_to_connections

class Command(DumpData):
    help = 'dumpdata with greenhouse database'
    
    def handle(self, *args, **options):
        add_db_to_connections(options['database'])
        super(Command, self).handle(*args, **options)
