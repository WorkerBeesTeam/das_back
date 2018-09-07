from django.core.management.base import BaseCommand
from django.core.management import call_command

from applications import add_db_to_connections
from applications.house_list.models import House

class Command(BaseCommand):
    help = 'Remove old logs from all databases'
    
    def handle(self, *args, **options):
        call_command('removeold')
        
        house_list = House.objects.all()
        for house in house_list:
            add_db_to_connections(house.name)
            call_command('removeold', '--database', house.name)
