import uuid

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import connection

from applications import add_db_to_connections
from applications.scheme_list.models import Scheme, Scheme_Group
from . import sync_child_db

class Command(BaseCommand):
    help = 'Add device scheme and create database for it'
    
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
                teams.append(Scheme_Group.objects.get(id=int(team_id)))
        if team_name_list:
            for team_name in team_name_list:
                try:
                    teams.append(Scheme_Group.objects.get(name=team_name))
                except:
                    print('Add team "' + team_name + '" ? [y/N]')
                    answer = input()
                    if answer.lower()[0] == 'y':
                        team = Scheme_Group()
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
            scheme = Scheme.objects.get(name=options['name'])
        except Scheme.DoesNotExist:
            # device = uuid.UUID(options['device']) if options['device'] else uuid.uuid4()
            scheme = Scheme()
            scheme.name = options['name']
            scheme.title = options['title']
            if not scheme.title:
                scheme.title = scheme.name
            scheme.latin_name = scheme.name
            if options['description']:
                scheme.description = options['description']

        conn = add_db_to_connections(scheme.name)
        
        with connection.cursor() as c:
            c.execute("CREATE SCHEMA /*!32312 IF NOT EXISTS*/ `{0}` DEFAULT CHARACTER SET utf8;".format(conn['NAME']))
            
        is_new_proj = scheme.pk == None
        try:
            call_command('migrate', '--settings', 'schemes.settings.prod', '--database', scheme.name, 'scheme')
            print('Database create: Ok')

            if is_new_proj:
                scheme.save()

                for team in teams:
                    scheme.teams.add(team)
                scheme.save()

                print("New scheme {0} added with id: {1}.".format(scheme.title, scheme.id))

                parent = None
                if options['parent_id']:
                    parent = Scheme.objects.get(id=options['parent_id'])
                elif options['parent_name']:
                    parent = Scheme.objects.get(name=options['parent_name'])

                if parent:
                    sync_child_db.Command().sync_data(scheme.name, parent.name)
                    scheme.parent = parent
                    scheme.save()

        except Exception as e:
            print(e)
            with connection.cursor() as c:
                c.execute("DROP DATABASE `{0}`;".format(conn['NAME']))
            if is_new_proj and scheme.pk:
                scheme.delete()

