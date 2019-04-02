from django.conf.urls import url

from rest_framework import routers  
from applications.api.v1 import viewsets

api_router = routers.SimpleRouter()
api_router.register('team', viewsets.TeamViewSet, base_name='team')
api_router.register('house', viewsets.HouseViewSet, base_name='house')
api_router.register('events', viewsets.EventLogViewSet, base_name='events')
api_router.register('logs', viewsets.LogViewSet, base_name='logs')
api_router.register('detail', viewsets.HouseDetailViewSet, base_name='detail')
#api_router.register('users', viewsets.UserViewSet)
api_router.register('code', viewsets.CodeViewSet, base_name='code')
api_router.register('checkers', viewsets.CheckerTypeViewSet, base_name='checkers')

urlpatterns = [
    url(r'^write_item_file/$', viewsets.FileUploadView.as_view()),
]

urlpatterns += api_router.urls
