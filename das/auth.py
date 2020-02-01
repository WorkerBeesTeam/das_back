import json
from django.contrib.auth.models import Permission

from rest_framework import serializers
from rest_framework_jwt.utils import jwt_payload_handler as jwt_payload_handler_origin

# for tg_auth
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from . import models

class User_Serializer(serializers.ModelSerializer):

    class Meta:
        model = models.User
        fields = ('id', 'username', 'password', 'email', 'first_name', 'last_name', 'need_to_change_password', 'phone_number')
        extra_kwargs = {
          'id': {'read_only': True},
          'password': {'write_only': True},
        }

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )

        user.set_password(validated_data['password'])
        user.save()

        return user

def jwt_response_payload_handler(token, user=None, request=None):
    data = User_Serializer(user, context={'request': request}).data
    data['token'] = token
    if user:
        permissions = None
        if user.is_superuser:
            permissions = Permission.objects.all()
        else:
            permissions = user.user_permissions.all() | Permission.objects.filter(group__user=user)

        if permissions:
            data['permissions'] = [x.codename for x in permissions]
    return data

def jwt_payload_handler(user):
    res = jwt_payload_handler_origin(user)
    res['groups'] = list(user.scheme_groups.values_list('group_id', flat=True))
    return res

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def tg_auth(req):
    if req.method != "POST":
        return show_main(req)

    try:
        json_data = json.loads(req.body.decode('utf-8'))
        token = json_data["token"]
        auth = list_models.Tg_Auth.objects.get(token=token)
    except (list_models.Tg_Auth.DoesNotExist, KeyError) as e:
        return HttpResponse("Bad request: " + str(e), status=400)
    
    auth.tg_user.user = req.user
    auth.tg_user.save()
    auth.delete()
    
    return HttpResponse(status=204)

