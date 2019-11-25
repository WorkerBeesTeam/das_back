import time
import subprocess
import json
import os
import git

from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.core import serializers
import django_filters
from django_filters.rest_framework.backends import DjangoFilterBackend

#from django_filters import rest_framework as filters
from rest_framework import status, filters, viewsets, views, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser
import rest_framework_filters as rf_filters

from applications import add_db_to_connections, get_current_language
from applications.house import models as houseModels
from applications.house_list import models as hListModels
from applications.house_list.tool import checkConnection
from applications.api.v1 import serializers as houseSerializers

class ChangeUserDetailsView(generics.UpdateAPIView):
    """
    An endpoint for changing user details
    """
    serializer_class = houseSerializers.ChangePasswordSerializer
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

class ChangePasswordView(generics.UpdateAPIView):
    """
    An endpoint for changing password.
    """
    serializer_class = houseSerializers.ChangePasswordSerializer
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
            self.object.save()
            return Response("Success.", status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_200_OK) # HTTP_400_BAD_REQUEST

class SaveTimerViewSet(viewsets.ModelViewSet): 
    serializer_class = houseSerializers.SaveTimerSerializer
    def get_queryset(self):
        conn_name = checkConnection(self.request)[1]
        return houseModels.Save_Timer.objects.using(conn_name).all()
        
class ViewItemViewSet(viewsets.ModelViewSet): 
    serializer_class = houseSerializers.ViewItemSerializer
    def get_queryset(self):
        conn_name = checkConnection(self.request)[1]
        view_id = self.request.GET.get('view_id')
        return houseModels.ViewItem.objects.using(conn_name).filter(view_id=view_id)
        
class TeamViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    def list(self, request):
        house, conn_name = checkConnection(self.request)
        values = house.teams.values_list('employee__user_id', 'employee__user__username','employee__user__first_name','employee__user__last_name')
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


class CityViewSet(viewsets.ModelViewSet):
    queryset = hListModels.City.objects.all()
    serializer_class = houseSerializers.CitySerializer

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = hListModels.Company.objects.all()
    serializer_class = houseSerializers.CompanySerializer

class HouseFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(name='name', lookup_expr='icontains')
    title = django_filters.CharFilter(name='title', lookup_expr='icontains')
    description = django_filters.CharFilter(name='description', lookup_expr='icontains')
    address = django_filters.CharFilter(name='address', lookup_expr='icontains')
    city = django_filters.CharFilter(name='city__name', lookup_expr='icontains')
    company = django_filters.CharFilter(name='company__name', lookup_expr='icontains')
    city__id = django_filters.NumberFilter()
    company__id = django_filters.NumberFilter()

    class Meta:
        model = hListModels.House
        fields = ['name', 'title', 'description','address','city','company','city__id','company__id']

class HouseViewSet(viewsets.ModelViewSet): 
#    queryset = hListModels.House.objects.using(conn_name).all().order_by('-lastUsage')
#    filter_backends = (filters.DjangoFilterBackend,)
#    filter_fields = ('name', 'name')
    serializer_class = houseSerializers.HouseSerializer
    #filter_backends = (filters.SearchFilter,filters.OrderingFilter)
    filter_backends = (DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter)
    filter_class = HouseFilter
    search_fields = ('name', 'title', 'description', 'city__name', 'company__name')
#    filter_fields = ('name', 'title', 'description', 'city__name', 'company__name', 'city_id', 'company_id')

    lookup_field = 'name'
    def get_queryset(self):
        return self.request.user.employee.team.in_team.all()

class FileUploadView(views.APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser,)

    def put(self, req, format=None):
        checkConnection(req)

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
        obj.write_item_file(project_id, user_id, devitem_id, file_name, file_path, dbus_interface='ru.deviceaccess.Dai.Server.iface')

        #print(subprocess.run(['/usr/bin/sudo', '/bin/sh', '-c', '/opt/test.sh'], capture_output=True))
        #args = ['/usr/bin/sudo', settings.DAI_SERVER_PATH, '-l', '--user_id', user_id, '--project_id', project_id, '--devitem_id', devitem_id, '--send_file', file_path, '--send_file_name', file_name]
        #ret = subprocess.run(args, capture_output=True)
        #if ret.returncode != 0:
        #    print(ret)
        #    print('Failed upload device item file')
        return Response(status=204)

class Log_Event_ViewSet(viewsets.ModelViewSet): 
#    queryset = houseModels.EventLog.objects.using(conn_name).all()
    serializer_class = houseSerializers.Log_Event_Serializer
    filter_backends = (filters.SearchFilter,filters.OrderingFilter,)
    search_fields = ('text', 'category')
    permission_classes = (AllowAny,)
    def get_queryset(self):
        conn_name = checkConnection(self.request)[1]

        try:
            ts_from = int(self.request.GET.get('ts_from'))
            ts_to = int(self.request.GET.get('ts_to'))
            if pk_from != 0 and pk_to != 0:
                return houseModels.Log_Event.objects.using(conn_name).filter(timestamp_msecs__range=[ts_from,ts_to])
        except:
            pass

        return houseModels.Log_Event.objects.using(conn_name).all()

# ---------------------- Log Data 2

class LDVS2_Filter(django_filters.FilterSet):
    #name = django_filters.CharFilter(name='name', lookup_expr='icontains')
    #title = django_filters.CharFilter(name='title', lookup_expr='icontains')
    #description = django_filters.CharFilter(name='description', lookup_expr='icontains')
    #address = django_filters.CharFilter(name='address', lookup_expr='icontains')
    #city = django_filters.CharFilter(name='city__name', lookup_expr='icontains')
    #company = django_filters.CharFilter(name='company__name', lookup_expr='icontains')
    #city__id = django_filters.NumberFilter()
    #company__id = django_filters.NumberFilter()
    min_ts = django_filters.NumberFilter(name="timestamp_msecs", lookup_expr='gte')
    max_ts = django_filters.NumberFilter(name="timestamp_msecs", lookup_expr='lte')
    timestamp_msecs = django_filters.NumberFilter()
    item__type__title = django_filters.NumberFilter()
    item__name = django_filters.NumberFilter()
    item__group__title = django_filters.NumberFilter()
    item__group__type__title = django_filters.NumberFilter()
    item__group__section__name = django_filters.NumberFilter()

    class Meta:
        model = houseModels.Log_Data
        #fields = ['name', 'title', 'description','address','city','company','city__id','company__id']
        fields = ['timestamp_msecs', 'min_ts', 'max_ts', 'item__type__title', 'item__name', 'item__group__title', 'item__group__type__title', 'item__group__section__name']

class Log_Data_ViewSet_2(viewsets.ModelViewSet): 
#    queryset = houseModels.EventLog.objects.using(conn_name).all()
    serializer_class = houseSerializers.Log_Data_Serializer_2
    filter_backends = (DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter)
    filter_class = LDVS2_Filter
    filterset_class = LDVS2_Filter
    search_fields = ('item__type__title', 'item__name', 'item__group__title', 'item__group__type__title', 'item__group__section__name')
    permission_classes = (AllowAny,)
    def get_queryset(self):
        #conn_name = checkConnection(self.request, 9)[1]
        conn_name = checkConnection(self.request)[1]

        try:
            ts_from = int(self.request.GET.get('ts_from'))
            ts_to = int(self.request.GET.get('ts_to'))
            if pk_from != 0 and pk_to != 0:
                return houseModels.Log_Data.objects.using(conn_name).filter(timestamp_msecs__range=[ts_from,ts_to])
        except:
            pass

        return houseModels.Log_Data.objects.using(conn_name).all()

# ------------------- Logs -------------------------
class ItemTypeFilter(rf_filters.FilterSet):
    class Meta:
        model = houseModels.ItemType
        fields = {'groupType_id'}

def devitem_types(request):
    conn_name = checkConnection(request)[1]
    return houseModels.ItemType.objects.using(conn_name).all()

class DeviceItemFilter(rf_filters.FilterSet):
    type = rf_filters.RelatedFilter(ItemTypeFilter, name='type', queryset=devitem_types)
    class Meta:
        model = houseModels.DeviceItem
        fields = ['type']

def device_items(req):
    conn_name = checkConnection(req)[1]
    return houseModels.DeviceItem.objects.using(conn_name).all()

class LogDateFilter(django_filters.FilterSet):
    date = rf_filters.DateTimeFromToRangeFilter()
    item = rf_filters.RelatedFilter(DeviceItemFilter, name='item', queryset=device_items)

    class Meta:
        model = houseModels.Logs
        fields = ['date', 'item']

class Log_Data_ViewSet(viewsets.ModelViewSet): 
    serializer_class = houseSerializers.Log_Data_Serializer
#    filter_backends = (filters.OrderingFilter,)
#    filter_backends = (rf_filters.backends.DjangoFilterBackend,)
#    filter_class = LogDateFilter
#    permission_classes = (AllowAny,)
    def get_queryset(self):
#        from applications import add_db_to_connections
#        add_db_to_connections('baltika0')
#        return houseModels.Logs.objects.using('baltika0').all()
        conn_name = checkConnection(self.request)[1]

        ts_from = self.request.GET.get('ts_from', '')
        ts_to = self.request.GET.get('ts_to', '')
        items_string = self.request.GET.get('items', None)
        if items_string:
            item_strings = items_string.split(',')
            items = []
            for item in item_strings:
                items.append(int(item))
            if items:
                return houseModels.Log_Data.objects.using(conn_name).filter(item_id__in=items, timestamp_msecs__range=[ts_from, ts_to]).order_by('timestamp_msecs')

        itemtypes_string = self.request.GET.get('itemtypes', None)
        if itemtypes_string:
            item_strings = itemtypes_string.split(',')
            items = []
            for item in item_strings:
                items.append(int(item))
            if items:
                return houseModels.Log_Data.objects.using(conn_name).filter(item__type_id__in=items, timestamp_msecs__range=[ts_from, ts_to]).order_by('timestamp_msecs')

        group_type = int(self.request.GET.get('group_type', 0))
        return houseModels.Log_Data.objects.using(conn_name).filter(item__type__groupType_id=group_type, timestamp_msecs__range=[ts_from, ts_to]).order_by('timestamp_msecs')
# ------------------- END Logs -------------------------

class HouseDetailViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    def list(self, request):
        house = get_object_or_404(hListModels.House, name=request.GET.get('project_name', ''), teams__pk=request.user.employee.team_id)
        conn_name = house.name
        add_db_to_connections(conn_name)

        sct_qset = houseModels.Section.objects.using(conn_name).all()
        sct_srlz = houseSerializers.SectionSerializer(sct_qset, many=True)

        dev_qset = houseModels.Device.objects.using(conn_name).all()
        dev_srlz = houseSerializers.DeviceSerializer(dev_qset, many=True)

        groupType_qset = houseModels.GroupType.objects.using(conn_name).all()
        groupType_srlz = houseSerializers.GroupTypeSerializer(groupType_qset, many=True)

        groupMode_qset = houseModels.GroupMode.objects.using(conn_name).all()
        groupMode_srlz = houseSerializers.GroupModeSerializer(groupMode_qset, many=True)
        
        itemType_qset = houseModels.ItemType.objects.using(conn_name).all()
        itemType_srlz = houseSerializers.ItemTypeSerializer(itemType_qset, many=True)
        
        signType_qset = houseModels.SignType.objects.using(conn_name).all()
        signType_srlz = houseSerializers.SignTypeSerializer(signType_qset, many=True)

        statusType_qset = houseModels.StatusType.objects.using(conn_name).all()
        statusType_srlz = houseSerializers.StatusTypeSerializer(statusType_qset, many=True)

        statuses_qset = houseModels.Status.objects.using(conn_name).all()
        statuses_srlz = houseSerializers.StatusesSerializer(statuses_qset, many=True)

        param_qset = houseModels.ParamItem.objects.using(conn_name).all()
        param_srlz = houseSerializers.ParamItemSerializer(param_qset, many=True)

        view_qset = houseModels.View.objects.using(conn_name).all()
        view_srlz = houseSerializers.ViewSerializer(view_qset, many=True)

        house.lastUsage = timezone.now()
        house.save()
        
        current_lang = get_current_language(request)
        if current_lang != 'ru':
            try:
                translations = houseModels.Translation.objects.using(conn_name).get(lang=current_lang)
                translations_dict = json.loads(translations.data)
                scts_tr = translations_dict.get('sections', None)
                groups_tr = translations_dict.get('groups', None)
                self.translate_sections(sct_srlz.data, scts_tr, groups_tr)
                 
                devices_tr = translations_dict.get('devices', None)
                items_tr = translations_dict.get('items', None)
                self.translate_devices(dev_srlz.data, devices_tr, items_tr)

                params_tr = translations_dict.get('params', None)
                self.translate_objs(param_srlz.data, params_tr, 'title', 'description')

                groupTypes_tr = translations_dict.get('groupTypes', None)
                self.translate_objs(groupType_srlz.data, groupTypes_tr, 'title', 'description')
  
                groupModes_tr = translations_dict.get('groupModes', None)
                self.translate_objs(groupMode_srlz.data, groupModes_tr, 'title')

                itemTypes_tr = translations_dict.get('itemTypes', None)
                self.translate_objs(itemType_srlz.data, itemTypes_tr, 'title')

                signTypes_tr = translations_dict.get('signTypes', None)
                self.translate_objs(signType_srlz.data, signTypes_tr, 'name')

                statusTypes_tr = translations_dict.get('statusTypes', None)
                self.translate_objs(statusType_srlz.data, statusTypes_tr, 'title')

                statuses_tr = translations_dict.get('statuses', None)
                self.translate_objs(statuses_srlz.data, statuses_tr, 'text')

                views_tr = translations_dict.get('views', None)
                self.translate_objs(view_srlz.data, views_tr, 'name')

            except houseModels.Translation.DoesNotExist:
                print('Oops! There is no translation for \'' + current_lang + '\' language')

        return Response({
            'id': house.id,
            'title': house.title,
            'sections': sct_srlz.data,
            'devices': dev_srlz.data,
            'params': param_srlz.data,
            'groupTypes': groupType_srlz.data,
            'groupModes': groupMode_srlz.data,
            'itemTypes': itemType_srlz.data,
            'signTypes': signType_srlz.data,
            'statusTypes': statusType_srlz.data,
            'statuses': statuses_srlz.data,
            'views': view_srlz.data
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

#    serializer_class = HouseDetailSerializer

#class UserViewSet(viewsets.ModelViewSet):
#    queryset = get_user_model().objects.using(conn_name).all()
#    serializer_class = houseSerializers.UserSerializer

class CheckerTypeViewSet(viewsets.ModelViewSet):
    serializer_class = houseSerializers.CheckerTypeSerializer
    def get_queryset(self):
        conn_name = checkConnection(self.request)[1]
        return houseModels.CheckerType.objects.using(conn_name).all()

class SectionViewSet(viewsets.ModelViewSet):
    serializer_class = houseSerializers.SectionSerializer
    def get_queryset(self):
        conn_name = checkConnection(self.request)[1]
        return houseModels.Section.objects.using(conn_name).all()

class CodeViewSet(viewsets.ViewSet):
    serializer_class = houseSerializers.CodeSerializer
    def get_queryset(self):
        conn_name = checkConnection(self.request)[1]
        return houseModels.Codes.objects.using(conn_name).all()

    def list(self, request):
        queryset = self.get_queryset()
        for code in queryset:
            if code.global_id:
                if not code.name:
                    try:
                        code.name = hListModels.Code.objects.get(pk=code.pk).name
                    except hListModels.Code.DoesNotExist:
                        pass
                code.text = ''

        data = self.serializer_class(queryset, many=True).data
        return Response(data)

    def retrieve(self, request, pk=None):
        code = get_object_or_404(self.get_queryset(), pk=pk)
        data = self.serializer_class(code).data

        if code.global_id:
            g_code = get_object_or_404(hListModels.Code, pk=code.global_id)
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
            g_code = get_object_or_404(hListModels.Code, pk=code.global_id)
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

        git_path += str(code_id)
        open(git_path, 'w', encoding="utf8").write(text)
        try:
            git_obj.git.add(git_path)
            git_obj.git.commit('-m', 'Save_' + str(code_id))
        except git.GitCommandError as exc:
            print('Git commit failed: {0}'.format(exc.stderr))

        print('git init ok')


class ProducerViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = hListModels.Producer.objects.all()
    serializer_class = houseSerializers.Producer_Serializer

class DistributorViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = hListModels.Distributor.objects.all()
    serializer_class = houseSerializers.Distributor_Serializer

class Brand2ViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = hListModels.Brand.objects.all()
    serializer_class = houseSerializers.Brand2_Serializer

class BrandViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = hListModels.Brand.objects.all()
    serializer_class = houseSerializers.Brand_Serializer
