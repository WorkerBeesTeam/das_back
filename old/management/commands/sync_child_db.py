import uuid

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import connection, connections

from applications import add_db_to_connections
from applications.scheme_list.models import Scheme, Scheme_Group
from applications.scheme import models

class Command(BaseCommand):
    help = 'Add device scheme and create database for it'
    
    def add_arguments(self, parser):        
        parser.add_argument('--id', help='ID родительского проектa')
        parser.add_argument('--name', help='Имя родительского проектa')
        parser.add_argument('--child-name', help='Имя проекта')

    
    def batch_migrate(self, model, dest_db, src_db):        
        conn = add_db_to_connections(dest_db)
        add_db_to_connections(src_db)
        # get a total of the objects to be copied
        count = model.objects.using(src_db).count()
        # nothing to do
        if not count:
            print('No %s objects to copy' % model._meta.verbose_name)
            return

        with connection.cursor() as c:
            c.execute("SET foreign_key_checks = 0;")
            c.execute("TRUNCATE TABLE `{0}`.`{1}`;".format(conn['NAME'], model._meta.db_table))
            c.execute("SET foreign_key_checks = 1;")

        items = model.objects.using(src_db).all().order_by('pk')

        item_count = 0
        # process in chunks, to handle models with lots of data
        for i in range(0, count, 1000):
            chunk_items = items[i:i + 1000]
            model.objects.using(dest_db).bulk_create(chunk_items)
            item_count += chunk_items.count()

        for m2mfield in model._meta.many_to_many:
            m2m_model = getattr(model, m2mfield.name).through
            self.batch_migrate(m2m_model, dest_db, src_db)

    def sync_data(self, dest, src):
        print('sync {0} to {1}'.format(src, dest))
        self.batch_migrate(models.Codes, dest, src)
        self.batch_migrate(models.SignType, dest, src)
        self.batch_migrate(models.Translation, dest, src)
        self.batch_migrate(models.GroupType, dest, src)
        self.batch_migrate(models.StatusType, dest, src)
        self.batch_migrate(models.Status, dest, src)
        self.batch_migrate(models.CheckerType, dest, src)
        self.batch_migrate(models.GroupMode, dest, src)
        self.batch_migrate(models.Section, dest, src)
        self.batch_migrate(models.Group, dest, src)
        self.batch_migrate(models.Save_Timer, dest, src)
        self.batch_migrate(models.ItemType, dest, src)
        self.batch_migrate(models.Device, dest, src)
        self.batch_migrate(models.DeviceItem, dest, src)
        self.batch_migrate(models.View, dest, src)
        self.batch_migrate(models.ViewItem, dest, src)
        self.batch_migrate(models.ParamItem, dest, src)
        self.batch_migrate(models.Group_Param, dest, src)
        connections[dest].close()
        connections[src].close()

    def handle(self, *args, **options):

        if options['id']:
            scheme = Scheme.objects.get(id=options['id'])
        elif options['name']:
            scheme = Scheme.objects.get(name=options['name'])

        if scheme:
            if options['child_name']:
                child = Scheme.objects.get(name=options['child_name'])
                self.sync_data(child.name, scheme.name)
            else:
                childs = scheme.children.all()
                for child in childs:
                    self.sync_data(child.name, scheme.name)

