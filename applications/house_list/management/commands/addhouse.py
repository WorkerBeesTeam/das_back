import uuid

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import connection

from applications import add_db_to_connections
from applications.house_list.models import House, Team
from . import sync_child_db

class Command(BaseCommand):
    help = 'Add device house and create database for it'
    
    def add_arguments(self, parser):        
        parser.add_argument('name', help='Латинский аналог имени, должен быть уникальным')
        parser.add_argument('--title', help='Имя русскими буквами')
        parser.add_argument('--device', help='UUID')
        parser.add_argument('--description', help='Описание')
        parser.add_argument('--team-id', nargs='+', help='ID группы пользователей')
        parser.add_argument('--team-name', nargs='+', help='Имя группы пользователей')
        parser.add_argument('--parent-id', help='ID родительского проектa')
        parser.add_argument('--parent-name', help='Имя родительского проектa')
    
    def get_teams(self, team_id_list, team_name_list):
        teams = []
        if team_id_list:
            for team_id in team_id_list:
                teams.append(Team.objects.get(id=int(team_id)))
        if team_name_list:
            for team_name in team_name_list:
                try:
                    teams.append(Team.objects.get(name=team_name))
                except:
                    print('Add team "' + team_name + '" ? [y/N]')
                    answer = input()
                    if answer.lower()[0] == 'y':
                        team = Team()
                        team.name = team_name
                        team.save()
                        teams.append(team)
        return teams

    def handle(self, *args, **options):
        teams = self.get_teams(options['team_id'], options['team_name'])
        if not teams:
            print("Ошибка: Добавьте информацию о группе пользователей")
            exit()

        try:
            house = House.objects.get(name=options['name'])
        except House.DoesNotExist:
            # device = uuid.UUID(options['device']) if options['device'] else uuid.uuid4()
            house = House()
            house.name = options['name']
            house.title = options['title']
            if not house.title:
                house.title = house.name
            house.latin_name = house.name
            if options['description']:
                house.description = options['description']

        conn = add_db_to_connections(house.name)
        
        with connection.cursor() as c:
            c.execute("CREATE SCHEMA /*!32312 IF NOT EXISTS*/ `{0}` DEFAULT CHARACTER SET utf8;".format(conn['NAME']))
            
        is_new_proj = house.pk == None
        try:
            call_command('migrate', '--settings', 'houses.settings.prod', '--database', house.name, 'house')
            print('Database create: Ok')

            if is_new_proj:
                house.save()

                for team in teams:
                    house.teams.add(team)
                house.save()

                print("New house {0} added with id: {1}.".format(house.title, house.id))

                if options['parent_id']:
                    parent = House.objects.get(id=options['parent_id'])
                elif options['parent_name']:
                    parent = House.objects.get(name=options['parent_name'])

                if parent:
                    sync_child_db.Command().sync_data(house.name, parent.name)
                    house.parent = parent
                    house.save()

        except Exception as e:
            print(e)
            with connection.cursor() as c:
                c.execute("DROP DATABASE `{0}`;".format(conn['NAME']))
            if is_new_proj and house.pk:
                house.delete()

