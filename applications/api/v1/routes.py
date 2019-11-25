from django.conf.urls import url

from rest_framework import routers  
from applications.api.v1 import viewsets

api_router = routers.SimpleRouter()
api_router.register('city', viewsets.CityViewSet, base_name='city')
api_router.register('company', viewsets.CompanyViewSet, base_name='company')
api_router.register('team', viewsets.TeamViewSet, base_name='team')
api_router.register('house', viewsets.HouseViewSet, base_name='house')
api_router.register('log_event', viewsets.Log_Event_ViewSet, base_name='log_event')
api_router.register('log_data', viewsets.Log_Data_ViewSet, base_name='log_data')
api_router.register('log_data_2', viewsets.Log_Data_ViewSet_2, base_name='log_data_2')
api_router.register('detail', viewsets.HouseDetailViewSet, base_name='detail')
#api_router.register('users', viewsets.UserViewSet)
api_router.register('code', viewsets.CodeViewSet, base_name='code')
api_router.register('checkers', viewsets.CheckerTypeViewSet, base_name='checkers')
api_router.register('viewitem', viewsets.ViewItemViewSet, base_name='viewitem')
api_router.register('savetimer', viewsets.SaveTimerViewSet, base_name='savetimer')
api_router.register('producer', viewsets.ProducerViewSet, base_name='producer')
api_router.register('distributor', viewsets.DistributorViewSet, base_name='distributor')
api_router.register('brand', viewsets.BrandViewSet, base_name='brand')
api_router.register('brand2', viewsets.Brand2ViewSet, base_name='brand2')

urlpatterns = [
    url(r'^write_item_file/$', viewsets.FileUploadView.as_view()),
    url(r'change_password/$', viewsets.ChangePasswordView.as_view()),
    url(r'change_user_details/$', viewsets.ChangeUserDetailsView.as_view()),
]

urlpatterns += api_router.urls
