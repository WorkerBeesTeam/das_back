import json
from rest_framework import serializers
from applications.house import models as houseModels
from applications.house_list import models as hListModels

from django.contrib.auth.password_validation import validate_password

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = hListModels.City
        fields = ['id', 'name']

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = hListModels.Company
        fields = ['id', 'name']

class SaveTimerSerializer(serializers.ModelSerializer):
    class Meta:
        model = houseModels.Save_Timer
        fields = ('id', 'interval')

class ViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = houseModels.View
        fields = ('id', 'name')

class ViewItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = houseModels.ViewItem
        fields = ('id', 'view_id', 'item_id')

class HouseSerializer(serializers.ModelSerializer):
#    device = UUIDField(format='hex_verbose')
#    company = CompanySerializer(many=False,read_only=False)
#    city = CitySerializer(many=False,read_only=False)
    class Meta:
        model = hListModels.House
        fields = ('id', 'name', 'device', 'lastUsage', 'title', 'description', 'address', 'city', 'company', 'parent', 'version')
        read_only_fields = ('id', 'name', 'device', 'lastUsage')

class ParamItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = houseModels.ParamItem
        fields = ('id', 'name', 'title', 'description', 'type', 'groupType_id', 'parent_id')

class GroupParamSerializer(serializers.ModelSerializer):
    value = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field='value'
    )
    class Meta:
        model = houseModels.Group_Param
        fields = ('id', 'value', 'group_id', 'param_id', 'parent_id')

class GroupModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = houseModels.GroupMode
        fields = ('id', 'name', 'group_type_id', 'title')

class GroupStatusSerializer(serializers.ModelSerializer):
    args = serializers.SerializerMethodField()

    def get_args(self, obj):
        if obj.args:
            return obj.args.split("\n")
        return []

    class Meta:
        model = houseModels.GroupStatus
        fields = ('status_id', 'args')

class GroupSerializer(serializers.ModelSerializer):
    params = GroupParamSerializer(many=True, read_only=True)
    mode = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field='mode_id'
     )
    statuses = GroupStatusSerializer(many=True, read_only=True)

    class Meta:
        model = houseModels.Group
        fields = ('id', 'title', 'type_id', 'params', 'mode', 'statuses')
  
#class GroupType(models.Model):
#    name = models.CharField(max_length=64)
#    title = models.CharField(max_length=32)
#    displayType = models.ForeignKey('ItemType', null=True, on_delete=models.SET_NULL)
#    code = models.ForeignKey(Codes, null=True, on_delete=models.SET_NULL)
#    description = models.CharField(max_length=1024, default='')
   
class GroupTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = houseModels.GroupType
        fields = ('id', 'name', 'title', 'code_id', 'description')

class ItemTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = houseModels.ItemType
        fields = ('id', 'name', 'title', 'isRaw', 'groupType_id', 'sign_id', 'registerType', 'saveAlgorithm', 'save_timer_id')

class SignTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = houseModels.SignType
        fields = '__all__'

class CheckerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = houseModels.CheckerType
        fields = '__all__'

class StatusTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = houseModels.StatusType
        fields = '__all__'

class StatusesSerializer(serializers.ModelSerializer):
    class Meta:
        model = houseModels.Status
        fields = ('id', 'groupType_id', 'type_id', 'name', 'text', 'inform')

class SectionSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)
    
    class Meta:
        model = houseModels.Section
        fields = ('id', 'name', 'dayStart', 'dayEnd', 'groups')

def normalize_value(val):
    try:
        if type(val) != str:
            raise

        if len(val) > 2 and ((val[0] == '[' and val[-1] == ']') or (val[0] == '{' and val[-1] == '}')):
            return json.loads(val)

        if val.lower() == 'true':
            return True
        elif val.lower() == 'false':
            return False

        try:
            val = int(val)
        except:
            val = float(val)

        if val != val:
            val = 'NaN'
    except:
        pass
    
    return val

class Device_Item_Value_Serializer(serializers.ModelSerializer):
    display = serializers.SerializerMethodField()
    raw = serializers.SerializerMethodField()

    def get_display(self, obj):
        return normalize_value(obj.display)
    
    def get_raw(self, obj):
        return normalize_value(obj.raw)

    class Meta:
        model = houseModels.Device_Item_Value
        fields = ('raw', 'display')

class DeviceItemSerializer(serializers.ModelSerializer):
    val = Device_Item_Value_Serializer(required=True)

    class Meta:
        model = houseModels.DeviceItem
        fields = ('id', 'name', 'type_id', 'extra', 'group_id', 'device_id', 'parent_id', 'val')

class CheckerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = houseModels.CheckerType
        fields = '__all__'

class DeviceSerializer(serializers.ModelSerializer):
    items = DeviceItemSerializer(many=True, read_only=True)

    class Meta:
        model = houseModels.Device
        fields = ('id', 'name', 'extra', 'checker_id', 'check_interval', 'items')

class Log_Event_Serializer(serializers.ModelSerializer):
    class Meta:
        model = houseModels.Log_Event
        fields = '__all__'

class LDS2_Type(serializers.ModelSerializer):
    class Meta:
        model = houseModels.ItemType
        fields = ('id','title')

class LDS2_Section(serializers.ModelSerializer):
    class Meta:
        model = houseModels.Section
        fields = ('id','name')

class LDS2_GroupType(serializers.ModelSerializer):
    class Meta:
        model = houseModels.GroupType
        fields = ('id','title')

class LDS2_Group(serializers.ModelSerializer):
    section = LDS2_Section()
    type = LDS2_GroupType()
    class Meta:
        model = houseModels.Group
        fields = ('id','title','section','type')

class LDS2_Item(serializers.ModelSerializer):
    type = LDS2_Type()
    group = LDS2_Group()
    class Meta:
        model = houseModels.DeviceItem
        fields = ('id','name','type','group')

class Log_Data_Serializer_2(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()
    raw_value = serializers.SerializerMethodField()

    def get_value(self, obj):
        return normalize_value(obj.value)
    
    def get_raw_value(self, obj):
        return normalize_value(obj.raw_value)

    item = LDS2_Item(many=False)
    class Meta:
        model = houseModels.Log_Data
        fields = ('timestamp_msecs', 'item', 'raw_value', 'value', 'user_id')


class Log_Data_Serializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()
    raw_value = serializers.SerializerMethodField()

    def get_value(self, obj):
        return normalize_value(obj.value)
    
    def get_raw_value(self, obj):
        return normalize_value(obj.raw_value)

    class Meta:
        model = houseModels.Log_Data
        fields = ('timestamp_msecs', 'item_id', 'raw_value', 'value')

class CodeSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(CodeSerializer, self).__init__(*args, **kwargs)
        if kwargs.get('many', False):
            self.fields.pop('text')

    class Meta:
        model = houseModels.Codes
        fields = ('id', 'name', 'text', 'global_id')

class Distributor_Serializer(serializers.ModelSerializer):
    class Meta:
        model = hListModels.Distributor
        fields = '__all__'

class Producer_Serializer(serializers.ModelSerializer):
    class Meta:
        model = hListModels.Producer
        fields = '__all__'

class Brand_Serializer(serializers.ModelSerializer):
    producer = Producer_Serializer()
    distributor = Distributor_Serializer()
    class Meta:
        model = hListModels.Brand
        fields = '__all__'

class Brand2_Serializer(serializers.ModelSerializer):
    class Meta:
        model = hListModels.Brand
        fields = '__all__'

"""
    def update(self, instance, validated_data):
        # Update the  instance
        instance.active = validated_data['active']
        instance.alc = validated_data['alc']
        instance.barcode = validated_data['barcode']
        instance.ingredients = validated_data['ingredients']
        instance

  active: boolean = true;
  alc: string;
  barcode: string;
  distributor: Distributor;
  id: number;
  ingredients: string;
  more_details: string;
  name: string;
  pressure: any;
  producer: Producer;
  storage_condition: string;

        instance.save()

        return instance
"""
