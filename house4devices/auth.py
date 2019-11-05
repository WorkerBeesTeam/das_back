from django.contrib.auth.models import User, Permission

from rest_framework import serializers
from rest_framework_jwt.utils import jwt_payload_handler as rfj_u_jph

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email', 'first_name', 'last_name')
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
    data = UserSerializer(user, context={'request': request}).data
    data['token'] = token
    if user:
        data['need_to_change_password'] = user.employee.need_to_change_password
        permissions = None
        if user.is_superuser:
            permissions = Permission.objects.all()
        else:
            permissions = user.user_permissions.all() | Permission.objects.filter(group__user=user)

        if permissions:
            data['permissions'] = [x.codename for x in permissions]
    return data

def jwt_payload_handler(user):
    res = rfj_u_jph(user)
    res['teams'] = [user.employee.team.id]
    #res['test'] = 'hello world!!!'
    return res
