from django.core.management.commands.loaddata import Command as LoadData

from applications import add_db_to_connections

class Command(LoadData):
    help = 'loaddata with greenhouse database'
    
    def handle(self, *args, **options):
        add_db_to_connections(options['database'])
        super(Command, self).handle(*args, **options)
