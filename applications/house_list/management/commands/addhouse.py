import uuid

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import connection

from applications import add_db_to_connections
from applications.house_list.models import House, Team

class Command(BaseCommand):
    help = 'Add device house and create database for it'
    
    def add_arguments(self, parser):        
        parser.add_argument('name', help='Латинский аналог имени, должен быть уникальным')
        parser.add_argument('--title', help='Имя русскими буквами')
        parser.add_argument('--device', help='UUID')
        parser.add_argument('--description', help='Описание')
        parser.add_argument('--team-id', help='ID группы пользователей')
        parser.add_argument('--team-name', help='Имя группы пользователей')
    
    def handle(self, *args, **options):
        try:
            house = House.objects.get(name=options['name'])
        except House.DoesNotExist:
            try:
                if options['team_id']:
                    team = Team.objects.get(id=options['team_id'])
                else:
                    team = Team.objects.get(name=options['team_name'])
            except Team.DoesNotExist:
                if options['team_name'] and not options['team_id']:
                    team = Team()
                    team.name = options['team_name']
                    team.save()
                    
                    print("New team {0} added with id: {1}.".format(team.name, team.id))
                else:
                    print("Ошибка: Добавьте информацию о группе пользователей")
                    exit()
                
            device = uuid.UUID(options['device']) if options['device'] else uuid.uuid4()

            house = House()
            house.title = options.get('title', options['name'])
            house.name = options['name']
            house.latin_name = house.name
            if options['description']:
                house.description = options['description']
            house.device = device
            house.team = team
            
        conn = add_db_to_connections(house.name)
        
        with connection.cursor() as c:
            c.execute("CREATE SCHEMA /*!32312 IF NOT EXISTS*/ `{0}` DEFAULT CHARACTER SET utf8;".format(conn['NAME']))
            
        try:
            call_command('migrate', '--settings', 'houses.settings.prod', '--database', house.name, 'house')
            print('Database create: Ok')

            if house.pk == None:
                house.save()
                house.teams.add(team)
                house.save()

                print("New house {0} added with id: {1}.".format(house.title, house.id))
                print("Device: {0}".format(str(device)))
        except Exception as e:
            print(e)
            with connection.cursor() as c:
                c.execute("DROP DATABASE `{0}`;".format(conn['NAME']))
