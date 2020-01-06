from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.contrib.auth.models import User
from django.db import connections

from applications import add_db_to_connections
from applications.house_list.models import House

class Command(BaseCommand):
    help = 'Make and migrate for all databases'
    
    def add_arguments(self, parser):        
        parser.add_argument('name', help='Латинский аналог имени, должен быть уникальным')

    def handle(self, *args, **options):
        house_name = options['name']
        add_db_to_connections(house_name)
            
        self.make_and_migrate(house_name)

    def make_and_migrate(self, db_id):
        call_command('migrate', '--database', db_id, 'house')
                
