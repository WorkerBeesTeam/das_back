from django.core.management.base import BaseCommand
from rest_framework_jwt.serializers import VerifyJSONWebTokenSerializer #, ValidationError
from rest_framework.exceptions import ValidationError

import json

class Command(BaseCommand):
    help = 'Check authenticaion token'

    def add_arguments(self, parser):        
        parser.add_argument('token', help='Authentication token')
            
    def handle(self, *args, **options):
        data = {'token': options['token']}
        res = {}
        try:
            valid_data = VerifyJSONWebTokenSerializer().validate(data)
            user = valid_data['user']
            res['user'] = user.username
            res['is_staff'] = user.is_staff
            res['team'] = user.employee.team.id
            res['groups'] = list(user.groups.values())
#            res['houses'] = list(user.employee.team.in_team.values_list('id', flat=True))
        except ValidationError as ve:
            res['error'] = ve.detail
            res['token'] = options['token']
        except:
            res['error'] = ['Fail']

        print(json.dumps(res))
