from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.contrib.auth.models import User
from django.db import connections

from applications import add_db_to_connections
from applications.house_list.models import House

class Command(BaseCommand):
    help = 'Make and migrate for all databases'
    
    def handle(self, *args, **options):
        house_list = House.objects.all()
        for house in house_list:
            add_db_to_connections(house.name)
            
        self.all_make_and_migrate()

    def all_make_and_migrate(self):
        call_command('makemigrations')
        
        for db_id in connections.databases:
            if db_id == 'default':
                call_command('migrate')
            else:
                call_command('migrate', '--database', db_id, 'house')
                
