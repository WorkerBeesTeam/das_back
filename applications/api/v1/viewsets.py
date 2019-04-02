import time
import subprocess

from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
import django_filters

#from django_filters import rest_framework as filters
from rest_framework import filters, viewsets, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser
import rest_framework_filters as rf_filters

from applications import add_db_to_connections
from applications.house import models as houseModels
from applications.house_list import models as hListModels
from applications.house_list.tool import checkConnection
from applications.api.v1 import serializers as houseSerializers

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

class HouseViewSet(viewsets.ModelViewSet): 
#    queryset = hListModels.House.objects.using(conn_name).all().order_by('-lastUsage')
#    filter_backends = (filters.DjangoFilterBackend,)
#    filter_fields = ('name', 'name')
    serializer_class = houseSerializers.HouseSerializer
    filter_backends = (filters.SearchFilter,filters.OrderingFilter)
    search_fields = ('name', 'title', 'description')

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
        file_path = '/var/tmp/dai_item_file_' + str(time.time())
        file_path += '.dat'
        with open(file_path, 'wb+') as destination:
            for chunk in input_file.chunks():
                destination.write(chunk)
        
        args = ['/usr/bin/sudo', settings.DAI_SERVER_PATH, '-l', '--user_id', user_id, '--project_id', project_id, '--devitem_id', devitem_id, '--send_file', file_path, '--send_file_name', file_name]
        ret = subprocess.call(args)
        if ret != 0:
            print(ret)
            print('Failed upload device item file')
        return Response(status=204)

class EventLogViewSet(viewsets.ModelViewSet): 
#    queryset = houseModels.EventLog.objects.using(conn_name).all()
    serializer_class = houseSerializers.EventLogSerializer
    filter_backends = (filters.SearchFilter,filters.OrderingFilter,)
    search_fields = ('msg', 'who')
    permission_classes = (AllowAny,)
    def get_queryset(self):
        conn_name = checkConnection(self.request)[1]

        try:
            pk_from = int(self.request.GET.get('pk_from'))
            pk_to = int(self.request.GET.get('pk_to'))
            if pk_from != 0 and pk_to != 0:
                return houseModels.EventLog.objects.using(conn_name).filter(id__range=[pk_from,pk_to])
        except:
            pass

        return houseModels.EventLog.objects.using(conn_name).all()

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

class LogViewSet(viewsets.ModelViewSet): 
    serializer_class = houseSerializers.LogSerializer
#    filter_backends = (filters.OrderingFilter,)
#    filter_backends = (rf_filters.backends.DjangoFilterBackend,)
#    filter_class = LogDateFilter
#    permission_classes = (AllowAny,)
    def get_queryset(self):
#        from applications import add_db_to_connections
#        add_db_to_connections('baltika0')
#        return houseModels.Logs.objects.using('baltika0').all()
        conn_name = checkConnection(self.request)[1]

        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        items_string = self.request.GET.get('items', None)
        if items_string:
            item_strings = items_string.split(',')
            items = []
            for item in item_strings:
                items.append(int(item))
            if items:
                return houseModels.Logs.objects.using(conn_name).filter(item_id__in=items, date__range=[date_from, date_to]).order_by('date')

        itemtypes_string = self.request.GET.get('itemtypes', None)
        if itemtypes_string:
            item_strings = itemtypes_string.split(',')
            items = []
            for item in item_strings:
                items.append(int(item))
            if items:
                return houseModels.Logs.objects.using(conn_name).filter(item__type_id__in=items, date__range=[date_from, date_to]).order_by('date')

        group_type = int(self.request.GET.get('group_type', 0))
        return houseModels.Logs.objects.using(conn_name).filter(item__type__groupType_id=group_type, date__range=[date_from, date_to]).order_by('date')
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

        house.lastUsage = timezone.now()
        house.save()

        return Response({
            'id': house.id,
            'title': house.title,
            'sections': sct_srlz.data,
            'devices': dev_srlz.data,
            'params': param_srlz.data,
            'groupTypes': groupType_srlz.data,
            'itemTypes': itemType_srlz.data,
            'signTypes': signType_srlz.data,
            'statusTypes': statusType_srlz.data,
            'statuses': statuses_srlz.data,
            })
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
            if code.global_id and not code.name:
                try:
                    code.name = hListModels.Code.objects.get(pk=code.pk).name
                except hListModels.Code.DoesNotExist:
                    pass

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

        if code.global_id and request.data.get('text', None) != None:
            g_code = get_object_or_404(hListModels.Code, pk=code.global_id)
            g_code.text = request.data['text']
            g_code.save()

        serializer.save()
        return Response(serializer.data)
