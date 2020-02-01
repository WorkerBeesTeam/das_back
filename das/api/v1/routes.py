from django.conf.urls import url

from rest_framework import routers  
from das.api.v1 import viewsets

api_router = routers.SimpleRouter()
api_router.register('city', viewsets.City_View_Set, basename='city')
api_router.register('company', viewsets.Company_View_Set, basename='company')
api_router.register('scheme_group', viewsets.Scheme_Group_View_Set, basename='scheme_group')
api_router.register('scheme', viewsets.Scheme_View_Set, basename='scheme')
api_router.register('log_event', viewsets.Log_Event_View_Set, basename='log_event')
api_router.register('log_data', viewsets.Log_Data_View_Set, basename='log_data')
api_router.register('log_data_2', viewsets.Log_Data_View_Set_2, basename='log_data_2')
api_router.register('detail', viewsets.Scheme_Detail_View_Set, basename='detail')
#api_router.register('users', viewsets.User_View_Set)
api_router.register('code_item', viewsets.Code_Item_View_Set, basename='code_item')
api_router.register('plugin', viewsets.Plugin_Type_View_Set, basename='plugin')
api_router.register('savetimer', viewsets.Save_Timer_View_Set, basename='savetimer')

urlpatterns = [
    url(r'^write_item_file/$', viewsets.File_Upload_View.as_view()),
    url(r'change_password/$', viewsets.Change_Password_View.as_view()),
    url(r'change_user_details/$', viewsets.Change_User_Details_View.as_view()),
]

urlpatterns += api_router.urls
