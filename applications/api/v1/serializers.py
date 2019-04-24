import json
from rest_framework import serializers
from applications.house import models as houseModels
from applications.house_list import models as hListModels

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
    class Meta:
        model = hListModels.House
        fields = ('id', 'name', 'device', 'lastUsage', 'title', 'description')
        read_only_fields = ('id', 'name', 'device', 'lastUsage')

class ParamItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = houseModels.ParamItem
        fields = ('id', 'name', 'title', 'description', 'type', 'groupType_id', 'parent_id')

class ParamValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = houseModels.ParamValue
        fields = ('id', 'value', 'group_id', 'param_id')

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
    params = ParamValueSerializer(many=True, read_only=True)
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

class EventLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = houseModels.EventLog
        fields = '__all__'

class LogSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()
    raw_value = serializers.SerializerMethodField()

    def get_value(self, obj):
        return normalize_value(obj.value)
    
    def get_raw_value(self, obj):
        return normalize_value(obj.raw_value)

    class Meta:
        model = houseModels.Logs
        fields = ('date', 'item_id', 'raw_value', 'value')

class CodeSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(CodeSerializer, self).__init__(*args, **kwargs)
        if kwargs.get('many', False):
            self.fields.pop('text')

    class Meta:
        model = houseModels.Codes
        fields = ('id', 'name', 'text', 'global_id')
