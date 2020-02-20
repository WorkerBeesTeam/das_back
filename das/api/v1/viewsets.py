import time
import subprocess
import json
import os
# import git

from django.db.models import Count, Q
from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404, get_list_or_404
from django.contrib.auth import get_user_model
from django.core import serializers
import django_filters
from django_filters.rest_framework.backends import DjangoFilterBackend

#from django_filters import rest_framework as filters
from rest_framework import status, filters, viewsets, views, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser

from das.tools import get_scheme
from das.views import get_current_language
from das import models
from das.api.v1 import serializers as api_serializers

class Change_User_Details_View(generics.UpdateAPIView):
    """
    An endpoint for changing user details
    """
    serializer_class = api_serializers.Change_Password_Serializer
    model = get_user_model()
    permission_classes = ()

    def get_object(self, queryset=None):
        return self.request.user

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.first_name = request.data.get("first_name")
        self.object.last_name = request.data.get("last_name")
        self.object.employee.phone_number = request.data.get("phone_number")
        self.object.employee.save()
        self.object.save()
        return Response('Success.', status=status.HTTP_200_OK)

class Change_Password_View(generics.UpdateAPIView):
    """
    An endpoint for changing password.
    """
    serializer_class = api_serializers.Change_Password_Serializer
    model = get_user_model()
    permission_classes = (IsAuthenticated,)

    def get_object(self, queryset=None):
        return self.request.user

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_200_OK) # HTTP_400_BAD_REQUEST
            if serializer.data.get("new_password") == serializer.data.get("old_password"):
                return Response("New password is the same of old_password", status=status.HTTP_200_OK) # HTTP_400_BAD_REQUEST
            # set_password also hashes the password that the user will get
            self.object.set_password(serializer.data.get("new_password"))
            self.object.need_to_change_password = False
            self.object.save()
            return Response("Success.", status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_200_OK) # HTTP_400_BAD_REQUEST

class Save_Timer_View_Set(viewsets.ModelViewSet): 
    serializer_class = api_serializers.Save_Timer_Serializer
    def get_queryset(self):
        scheme = get_scheme(self.request)
        scheme_id = scheme.parent_id if scheme.parent_id else scheme.id
        return models.Save_Timer.objects.filter(scheme_id=scheme_id)

class Scheme_Group_View_Set(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    def list(self, request):
        print('get groups scheme_id: ' + self.request.GET.get('id', '0') + ' user_id: ' + str(request.user.id))
        scheme = get_scheme(self.request)
        print('2 get groups scheme_id: ' + self.request.GET.get('id', '0') + ' user_id: ' + str(request.user.id))
        values = scheme.groups.values_list('scheme_group_user__user_id', 'scheme_group_user__user__username','scheme_group_user__user__first_name','scheme_group_user__user__last_name')
        result = []
        for id,login,fname,lname in values:
            if id:
                name = ''
                if fname:
                    name = fname
                if lname:
                    if name:
                        name += ' '
                    name += lname
                if not name:
                    name = login
                result.append({ 'id': id, 'name': name })

        return Response({'count': len(result), 'results': result})


class City_View_Set(viewsets.ModelViewSet):
    serializer_class = api_serializers.City_Serializer

    def get_queryset(self):
        return models.City.objects.filter(scheme__groups__scheme_group_user__user_id=self.request.user.id).annotate(Count("id")).order_by('id')

class Company_View_Set(viewsets.ModelViewSet):
    serializer_class = api_serializers.Company_Serializer

    def get_queryset(self):
        return models.Company.objects.filter(scheme__groups__scheme_group_user__user_id=self.request.user.id).annotate(Count("id")).order_by('id')

class SchemeFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    title = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    address = django_filters.CharFilter(lookup_expr='icontains')
    city = django_filters.CharFilter(field_name='city__name', lookup_expr='icontains')
    company = django_filters.CharFilter(field_name='company__name', lookup_expr='icontains')
    city__id = django_filters.NumberFilter()
    company__id = django_filters.NumberFilter()

    class Meta:
        model = models.Scheme
        fields = ['name', 'title', 'description','address','city','company','city__id','company__id']

class Scheme_View_Set(viewsets.ModelViewSet): 
#    queryset = models.Scheme.objects.filter(scheme_id=scheme.id).order_by('-lastUsage')
#    filter_backends = (filters.DjangoFilterBackend,)
#    filter_fields = ('name', 'name')
    serializer_class = api_serializers.Scheme_Serializer
    #filter_backends = (filters.SearchFilter,filters.OrderingFilter)
    filter_backends = (DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter)
    filter_class = SchemeFilter
    search_fields = ('name', 'title', 'description', 'city__name', 'company__name')
#    filter_fields = ('name', 'title', 'description', 'city__name', 'company__name', 'city_id', 'company_id')

    lookup_field = 'name'
    def get_queryset(self):
        return models.Scheme.objects.filter(groups__scheme_group_user__user_id=self.request.user.id).annotate(Count("id")).order_by('id')

class File_Upload_View(views.APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser,)

    def put(self, req, format=None):
        scheme = get_scheme(req)

        user_id = str(req.user.id)
        project_id = req.GET.get('id')
        devitem_id = req.GET.get('item_id')
        input_file = req.FILES['fileKey']
        file_name = input_file.name
#        file_path = '/var/tmp/dai_item_file_' + str(time.time())
        file_path = '/opt/firmware/dai_item_file_' + str(time.time())
        file_path += '.dat'
        with open(file_path, 'wb+') as destination:
            for chunk in input_file.chunks():
                destination.write(chunk)
        
        import dbus
        obj = dbus.SystemBus().get_object('ru.deviceaccess.Dai.Server', '/')
        obj.write_item_file(project_id, user_id, devitem_id, file_name, file_path, dbus_interface='ru.deviceaccess.Dai.iface')

        #print(subprocess.run(['/usr/bin/sudo', '/bin/sh', '-c', '/opt/test.sh'], capture_output=True))
        #args = ['/usr/bin/sudo', settings.DAI_SERVER_PATH, '-l', '--user_id', user_id, '--project_id', project_id, '--devitem_id', devitem_id, '--send_file', file_path, '--send_file_name', file_name]
        #ret = subprocess.run(args, capture_output=True)
        #if ret.returncode != 0:
        #    print(ret)
        #    print('Failed upload device item file')
        return Response(status=204)

class Log_Event_View_Set(viewsets.ModelViewSet): 
#    queryset = models.EventLog.objects.filter(scheme_id=scheme.id)
    serializer_class = api_serializers.Log_Event_Serializer
    filter_backends = (filters.SearchFilter,filters.OrderingFilter,)
    search_fields = ('text', 'category')
    permission_classes = (AllowAny,)
    def get_queryset(self):
        scheme = get_scheme(self.request)

        try:
            ts_from = int(self.request.GET.get('ts_from'))
            ts_to = int(self.request.GET.get('ts_to'))
            if pk_from != 0 and pk_to != 0:
                in_range = Q(timestamp_msecs__range=[ts_from,ts_to])
                one_scheme = Q(scheme_id=scheme.id)
                return models.Log_Event.objects.filter(in_range & one_scheme)
        except:
            pass

        return models.Log_Event.objects.filter(scheme_id=scheme.id)

# ---------------------- Log Data 2

class LDVS2_Filter(django_filters.FilterSet):
    #name = django_filters.CharFilter(lookup_expr='icontains')
    #title = django_filters.CharFilter(lookup_expr='icontains')
    #description = django_filters.CharFilter(lookup_expr='icontains')
    #address = django_filters.CharFilter(lookup_expr='icontains')
    #city = django_filters.CharFilter(lookup_expr='icontains')
    #company = django_filters.CharFilter(lookup_expr='icontains')
    #city__id = django_filters.NumberFilter()
    #company__id = django_filters.NumberFilter()
    min_ts = django_filters.NumberFilter(field_name="timestamp_msecs", lookup_expr='gte')
    max_ts = django_filters.NumberFilter(field_name="timestamp_msecs", lookup_expr='lte')
    timestamp_msecs = django_filters.NumberFilter()
    item__type__title = django_filters.NumberFilter()
    item__name = django_filters.NumberFilter()
    item__group_id = django_filters.NumberFilter()
    item__group__title = django_filters.NumberFilter()
    item__group__type__title = django_filters.NumberFilter()
    item__group__section__name = django_filters.NumberFilter()

    class Meta:
        model = models.Log_Value
        #fields = ['name', 'title', 'description','address','city','company','city__id','company__id']
        fields = ['timestamp_msecs', 'min_ts', 'max_ts', 'item__type__title', 'item__name', 'item__group__title', 'item__group__type__title', 'item__group__section__name','item__group_id']

class Log_Value_View_Set(viewsets.ModelViewSet): 
#    queryset = models.EventLog.objects.filter(scheme_id=scheme.id)
    serializer_class = api_serializers.Log_Value_Serializer
    filter_backends = (DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter)
    filter_class = LDVS2_Filter
    filterset_class = LDVS2_Filter
    search_fields = ('item__type__title', 'item__name', 'item__group__title', 'item__group__type__title', 'item__group__section__name')
    permission_classes = (IsAuthenticated,)
    def get_queryset(self):
        scheme = get_scheme(self.request)

        try:
            ts_from = int(self.request.GET.get('ts_from'))
            ts_to = int(self.request.GET.get('ts_to'))
            if pk_from != 0 and pk_to != 0:
                in_range = Q(timestamp_msecs__range=[ts_from,ts_to])
                one_scheme = Q(scheme_id=scheme.id)
                return models.Log_Value.objects.filter(in_range & one_scheme)
        except:
            pass

        return models.Log_Value.objects.filter(scheme_id=scheme.id)

# ------------------- Logs -------------------------
def devitem_types(request):
    scheme = get_scheme(request)
    scheme_id = scheme.parent_id if scheme.parent_id else scheme.id
    return models.ItemType.objects.filter(scheme_id=scheme_id)

def device_items(req):
    scheme = get_scheme(req)
    scheme_id = scheme.parent_id if scheme.parent_id else scheme.id
    return models.DeviceItem.objects.filter(scheme_id=scheme_id)

class Chart_Data_View_Set(viewsets.ModelViewSet): 
    serializer_class = api_serializers.Chart_Data_Serializer
#    filter_backends = (filters.OrderingFilter,)
#    permission_classes = (AllowAny,)

    CT_USER = 1
    CT_DIG_TYPE = 2
    CT_DEVICE_ITEM_TYPE = 3
    CT_DEVICE_ITEM = 4

    def get_queryset(self):
#        from applications import add_db_to_connections
#        add_db_to_connections('baltika0')
#        return models.Logs.objects.all()

        chart_type = int(self.request.GET['chart_type'])
        data = self.request.GET['data']

        scheme = get_scheme(self.request)
        one_scheme = Q(scheme_id=scheme.id)

        ts_from = self.request.GET['ts_from']
        ts_to = self.request.GET['ts_to']
        in_range = Q(timestamp_msecs__range=[ts_from,ts_to])

        if chart_type == self.CT_USER:
            return self.get_user_queryset(one_scheme, in_range, data)
        elif chart_type == self.CT_DIG_TYPE:
            return self.get_dig_type_queryset(one_scheme, in_range, int(data))
        if chart_type == self.CT_DEVICE_ITEM_TYPE:
            return self.get_device_item_type_queryset(one_scheme, in_range, data)
        if chart_type == self.CT_DEVICE_ITEM:
            return self.get_device_item_queryset(one_scheme, in_range, data)

        return None

    def get_user_queryset(self, q_scheme, q_time, data):
        return None

    def get_dig_type_queryset(self, q_scheme, q_time, group_type_id):
        in_items = Q(item__type__group_type_id=group_type_id)
        return models.Log_Value.objects.filter(q_time & in_items & q_scheme).order_by('timestamp_msecs')

    def get_device_item_type_queryset(self, q_scheme, q_time, itemtypes_string):
        item_strings = itemtypes_string.split(',')
        items = []
        for item in item_strings:
            items.append(int(item))
        if items:
            in_items = Q(item__type_id__in=items)
            return models.Log_Value.objects.filter(in_range & in_items & one_scheme).order_by('timestamp_msecs')
        return None

    def get_device_item_queryset(self, q_scheme, q_time, items_string):
        item_strings = items_string.split(',')
        items = []
        for item in item_strings:
            items.append(int(item))
        if items:
            in_items = Q(item_id__in=items)
            return models.Log_Value.objects.filter(in_range & in_items & one_scheme).order_by('timestamp_msecs')
        return None


# ------------------- END Logs -------------------------

class Scheme_Detail_View_Set(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    #def retrieve(self, request, pk=None):
    def list(self, request):
        scheme = get_list_or_404(models.Scheme, name=request.GET.get('name', None), groups__scheme_group_user__user_id=self.request.user.id)[0]
        scheme_id = scheme.parent_id if scheme.parent_id else scheme.id

        section_qset = models.Section.objects.filter(scheme_id=scheme_id)
        section_srlz = api_serializers.Section_Serializer(section_qset, many=True, context={'real_scheme_id': scheme.id})

        device_qset = models.Device.objects.filter(scheme_id=scheme_id)
        device_srlz = api_serializers.Device_Serializer(device_qset, many=True, context={'real_scheme_id': scheme.id})

        dig_type_qset = models.DIG_Type.objects.filter(scheme_id=scheme_id)
        dig_type_srlz = api_serializers.DIG_Type_Serializer(dig_type_qset, many=True)

        dig_mode_type_qset = models.DIG_Mode_Type.objects.filter(scheme_id=scheme_id)
        dig_mode_type_srlz = api_serializers.DIG_Mode_Type_Serializer(dig_mode_type_qset, many=True)
        
        device_item_type_qset = models.Device_Item_Type.objects.filter(scheme_id=scheme_id)
        device_item_type_srlz = api_serializers.Device_Item_Type_Serializer(device_item_type_qset, many=True)
        
        sign_type_qset = models.Sign_Type.objects.filter(scheme_id=scheme_id)
        sign_type_srlz = api_serializers.Sign_Type_Serializer(sign_type_qset, many=True)

        dig_status_category_qset = models.DIG_Status_Category.objects.filter(scheme_id=scheme_id)
        dig_status_category_srlz = api_serializers.DIG_Status_Category_Serializer(dig_status_category_qset, many=True)

        dig_status_type_qset = models.DIG_Status_Type.objects.filter(scheme_id=scheme_id)
        dig_status_type_srlz = api_serializers.DIG_Status_Type_Serializer(dig_status_type_qset, many=True)

        dig_param_type_qset = models.DIG_Param_Type.objects.filter(scheme_id=scheme_id)
        dig_param_type_srlz = api_serializers.DIG_Param_Type_Serializer(dig_param_type_qset, many=True)

        scheme.last_usage = timezone.now()
        scheme.save()
        
        current_lang = get_current_language(request)
        if current_lang != 'ru':
            try:
                translations = models.Translation.objects.get(lang=current_lang, scheme_id=scheme_id)
                translations_dict = json.loads(translations.data)
                section_tr = translations_dict.get('section', None)
                device_item_group_tr = translations_dict.get('device_item_group', None)
                self.translate_sections(section_srlz.data, section_tr, device_item_group_tr)
                 
                device_tr = translations_dict.get('device', None)
                device_item_tr = translations_dict.get('device_item', None)
                self.translate_devices(device_srlz.data, device_tr, device_item_tr)

                dig_param_type_tr = translations_dict.get('dig_param_type', None)
                self.translate_objs(dig_param_type_srlz.data, dig_param_type_tr, 'title', 'description')

                dig_type_tr = translations_dict.get('dig_type', None)
                self.translate_objs(dig_type_srlz.data, dig_types_tr, 'title', 'description')
  
                dig_mode_type_tr = translations_dict.get('dig_mode_type', None)
                self.translate_objs(dig_mode_type_srlz.data, dig_mode_type_tr, 'title')

                device_item_type_tr = translations_dict.get('device_item_type', None)
                self.translate_objs(device_item_type_srlz.data, device_item_types_tr, 'title')

                sign_type_tr = translations_dict.get('sign_type', None)
                self.translate_objs(sign_type_srlz.data, sign_type_tr, 'name')

                dig_status_category_tr = translations_dict.get('dig_status_category', None)
                self.translate_objs(dig_status_category_srlz.data, dig_status_category_tr, 'title')

                dig_status_type_tr = translations_dict.get('dig_status_type', None)
                self.translate_objs(dig_status_type_srlz.data, dig_status_type_tr, 'text')

            except models.Translation.DoesNotExist:
                print('Oops! There is no translation for \'' + current_lang + '\' language')

        return Response({
            'id': scheme.id,
            'title': scheme.title,
            'sign_type': sign_type_srlz.data,
            'section': section_srlz.data,
            'device': device_srlz.data,
            'device_item_type': device_item_type_srlz.data,
            'dig_param_type': dig_param_type_srlz.data,
            'dig_type': dig_type_srlz.data,
            'dig_mode_type': dig_mode_type_srlz.data,
            'dig_status_category': dig_status_category_srlz.data,
            'dig_status_type': dig_status_type_srlz.data
            })

    def translate_sections(self, sections, sections_tr, groups_tr):        
        for sec in sections:
            if sections_tr != None:
                for i, sec_tr in enumerate(sections_tr):
                    if sec_tr['id'] == sec['id']:
                        if 'name' in sec_tr and 'name' in sec:
                            sec['name'] = sec_tr['name']
                        del sections_tr[i]
                        break
            groups = sec['groups']
            self.translate_objs(groups, groups_tr, 'title')

    def translate_devices(self, devices, devices_tr, items_tr):
        for dev in devices:
            if devices_tr != None:
                for i, dev_tr in enumerate(devices_tr):
                    if dev_tr['id'] == dev['id']:
                        if 'name' in dev_tr and 'name' in dev:
                            dev['name'] = dev_tr['name']
                        del devices_tr[i]
                        break
            items = dev['items']
            self.translate_objs(items, items_tr, 'name')

    def translate_objs(self, origin_list, tr_list, *replace_list):
        if tr_list == None or len(tr_list) == 0:
            return
        for obj in origin_list:
            for i, obj_tr in enumerate(tr_list):
                if obj_tr['id'] == obj['id']:
                    for item in replace_list:
                        if item in obj_tr and item in obj:
                            obj[item] = obj_tr[item]
                    del tr_list[i]
                    break

#    serializer_class = SchemeDetail_Serializer

#class User_View_Set(viewsets.ModelViewSet):
#    queryset = get_user_model().objects.filter(scheme_id=scheme.id)
#    serializer_class = api_serializers.User_Serializer

class Plugin_Type_View_Set(viewsets.ModelViewSet):
    serializer_class = api_serializers.Plugin_Type_Serializer
    def get_queryset(self):
        scheme = get_scheme(self.request)
        scheme_id = scheme.parent_id if scheme.parent_id else scheme.id
        return models.Plugin_Type.objects.filter(scheme_id=scheme_id)

class Section_View_Set(viewsets.ModelViewSet):
    serializer_class = api_serializers.Section_Serializer
    def get_queryset(self):
        scheme = get_scheme(self.request)
        scheme_id = scheme.parent_id if scheme.parent_id else scheme.id
        return models.Section.objects.filter(scheme_id=scheme_id)

class Code_Item_View_Set(viewsets.ViewSet):
    serializer_class = api_serializers.Code_Item_Serializer
    def get_queryset(self):
        scheme = get_scheme(self.request)
        scheme_id = scheme.parent_id if scheme.parent_id else scheme.id
        return models.Code_Item.objects.filter(scheme_id=scheme_id)

    def list(self, request):
        queryset = self.get_queryset()
        for code in queryset:
            if code.global_id:
                if not code.name:
                    try:
                        code.name = models.Code.objects.get(pk=code.pk).name
                    except models.Code.DoesNotExist:
                        pass
                code.text = ''

        data = self.serializer_class(queryset, many=True).data
        return Response(data)

    def retrieve(self, request, pk=None):
        code = get_object_or_404(self.get_queryset(), pk=pk)
        data = self.serializer_class(code).data

        if code.global_id:
            g_code = get_object_or_404(models.Code, pk=code.global_id)
            data['text'] = g_code.text
            if not data['name']:
                data['name'] = g_code.name
        return Response(data)

    def partial_update(self, request, pk=None):
        code = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.serializer_class(code, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if code.global_id and request.data.get('text', None) != None:
            g_code = get_object_or_404(models.Code, pk=code.global_id)
            g_code.text = request.data['text']
            g_code.save()
            self.save_git(g_code.id, request.data['text'])
        else:
            self.save_git(code.id, request.data['text'], request.GET['id'])

        return Response(serializer.data)

    def save_git(self, code_id, text, proj_id=None):
        git_path = settings.FRONTEND_ROOT + '/../codes/'

        if proj_id:
            git_path += 'proj/' + str(proj_id) + '/'
        else:
            git_path += 'list_code/'

        os.makedirs(git_path, exist_ok=True)
        try:
            git_obj = git.Repo(git_path)
        except:
            git_obj = git.Repo.init(git_path)

        git_path += str(code_id) + '.js'
        open(git_path, 'w', encoding="utf8").write(text)
        try:
            git_obj.git.add(git_path)
            git_obj.git.commit('-m', 'Save_' + str(code_id))
        except git.GitCommandError as exc:
            print('Git commit failed: {0}'.format(exc.stderr))

        print('git init ok')

