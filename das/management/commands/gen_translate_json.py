import json

from django.core.management.base import BaseCommand
from django.db.models import Q

from das import models

class Command(BaseCommand):
    help = 'Generate random sekret key'

    def add_arguments(self, parser):        
        parser.add_argument('scheme', help='ИД или имя схемы')

    def handle(self, *args, **options):
        try:
            scheme = models.Scheme.objects.get(pk=int(options['scheme']))
        except ValueError:
            scheme = models.Scheme.objects.get(name=options['scheme'])

        data = {
            'section': list(models.Section.objects.filter(scheme_id=scheme.id).values('id', 'name')),
            'dig': list(models.Device_Item_Group.objects.filter(scheme_id=scheme.id).exclude(title='').values('id', 'title')),
            'device': list(models.Device.objects.filter(scheme_id=scheme.id).values('id', 'name')),
            'device_item': list(models.Device_Item.objects.filter(scheme_id=scheme.id).exclude(name='').values('id', 'name')),
            'dig_param_type': list(models.DIG_Param_Type.objects.filter(scheme_id=scheme.id).values('id', 'title', 'description')),
            'dig_type': list(models.DIG_Type.objects.filter(scheme_id=scheme.id).values('id', 'title', 'description')),
            'dig_mode_type': list(models.DIG_Mode_Type.objects.filter(scheme_id=scheme.id).values('id', 'title')),
            'device_item_type': list(models.Device_Item_Type.objects.filter(scheme_id=scheme.id).values('id', 'title')),
            'sign_type': list(models.Sign_Type.objects.filter(scheme_id=scheme.id).values('id', 'name')),
            'dig_status_category': list(models.DIG_Status_Category.objects.filter(scheme_id=scheme.id).values('id', 'title')),
            'dig_status_type': list(models.DIG_Status_Type.objects.filter(scheme_id=scheme.id).values('id', 'text')),
            'value_view': list(models.Value_View.objects.filter(scheme_id=scheme.id).values('type_id', 'view')),
        }


        print(json.dumps(data, indent=4, ensure_ascii=False))

