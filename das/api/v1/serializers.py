import json
from rest_framework import serializers
from das import models

from django.contrib.auth.password_validation import validate_password

class Change_Password_Serializer(serializers.Serializer):
    """
    Serializer for password change endpoint.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

class City_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.City
        fields = ['id', 'name']

class Company_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.Company
        fields = ['id', 'name']

class Save_Timer_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.Save_Timer
        fields = ('id', 'interval')

class Scheme_Serializer(serializers.ModelSerializer):
#    using_key = UUIDField(format='hex_verbose')
#    company = Company_Serializer(many=False,read_only=False)
#    city = City_Serializer(many=False,read_only=False)
    class Meta:
        model = models.Scheme
        fields = ('id', 'name', 'using_key', 'last_usage', 'title', 'description', 'address', 'city', 'company', 'parent', 'version')
        read_only_fields = ('id', 'name', 'using_key', 'last_usage')

class DIG_Param_Type_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.DIG_Param_Type
        fields = ('id', 'name', 'title', 'description', 'value_type', 'group_type_id', 'parent_id')

def param_normalize():
    pass

class DIG_Param_Serializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    def get_real_scheme_id(self, obj):
        p_name = 'real_scheme_id'
        return self.context[p_name] if p_name in self.context else obj.scheme_id

    def get_value(self, obj):
        value = None
        try:
            scheme_id = self.get_real_scheme_id(obj)
            p_value = models.DIG_Param_Value.objects.filter(scheme_id=scheme_id, group_param_id=obj.id).first()

            type = obj.param.value_type
            value = p_value.value if p_value else None
            param = models.DIG_Param_Type

            if type == param.VT_INT:
                return int(value)
            elif type == param.VT_BOOL:
                return str(value).lower() == 'true'
            elif type == param.VT_FLOAT:
                return float(value)
            else:
                return value
        except:
            pass
        return value if value is not None else ''
 
    class Meta:
        model = models.DIG_Param
        fields = ('id', 'value', 'group_id', 'param_id', 'parent_id')

class DIG_Mode_Type_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.DIG_Mode_Type
        fields = ('id', 'name', 'group_type_id', 'title')

class DIG_Status_Serializer(serializers.ModelSerializer):
    args = serializers.SerializerMethodField()

    def get_args(self, obj):
        if obj.args:
            return obj.args.split("\n")
        return []

    class Meta:
        model = models.DIG_Status
        fields = ('status_id', 'args')

class Device_Item_Group_Serializer(serializers.ModelSerializer):
    params = DIG_Param_Serializer(many=True, read_only=True)
    statuses = serializers.SerializerMethodField()
    mode = serializers.SerializerMethodField()

    def get_real_scheme_id(self, obj):
        p_name = 'real_scheme_id'
        return self.context[p_name] if p_name in self.context else obj.scheme_id

    def get_statuses(self, obj):
        scheme_id = self.get_real_scheme_id(obj)
        items = models.DIG_Status.objects.filter(scheme_id=scheme_id, group_id=obj.id)
        serializer = DIG_Status_Serializer(instance=items, many=True, read_only=True)
        return serializer.data

    def get_mode(self, obj):
        scheme_id = self.get_real_scheme_id(obj)
        try:
            mode_item = models.DIG_Mode.objects.get(scheme_id=scheme_id, group_id=obj.id)
            return mode_item.mode_id
        except models.DIG_Mode.DoesNotExist:
            pass
        return 0

    # mode = serializers.SlugRelatedField(
    #     many=False,
    #     read_only=True,
    #     slug_field='mode_id'
    #  )

    class Meta:
        model = models.Device_Item_Group
        fields = ('id', 'title', 'type_id', 'params', 'mode', 'statuses')
  
#class GroupType(models.Model):
#    name = models.CharField(max_length=64)
#    title = models.CharField(max_length=32)
#    displayType = models.ForeignKey('ItemType', null=True, on_delete=models.SET_NULL)
#    code = models.ForeignKey(Codes, null=True, on_delete=models.SET_NULL)
#    description = models.CharField(max_length=1024, default='')
   
class DIG_Type_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.DIG_Type
        fields = ('id', 'name', 'title', 'description')

class Device_Item_Type_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.Device_Item_Type
        fields = ('id', 'name', 'title', 'group_type_id', 'sign_id', 'register_type', 'save_algorithm', 'save_timer_id')

class Sign_Type_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.Sign_Type
        fields = '__all__'

class Plugin_Type_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.Plugin_Type
        fields = '__all__'

class DIG_Status_Category_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.DIG_Status_Category
        fields = '__all__'

class DIG_Status_Type_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.DIG_Status_Type
        fields = ('id', 'group_type_id', 'category_id', 'name', 'text', 'inform')

class Section_Serializer(serializers.ModelSerializer):
    groups = Device_Item_Group_Serializer(many=True, read_only=True)
    
    class Meta:
        model = models.Section
        fields = ('id', 'name', 'day_start', 'day_end', 'groups')

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
    value = serializers.SerializerMethodField()
    raw_value = serializers.SerializerMethodField()

    def get_value(self, obj):
        return normalize_value(obj.value)
    
    def get_raw_value(self, obj):
        return normalize_value(obj.raw_value)

    class Meta:
        model = models.Device_Item_Value
        fields = ('raw_value', 'value')

class Device_Item_Serializer(serializers.ModelSerializer):
    # val = Device_Item_Value_Serializer(read_only=True)
    val = serializers.SerializerMethodField()

    def get_real_scheme_id(self, obj):
        p_name = 'real_scheme_id'
        return self.context[p_name] if p_name in self.context else obj.scheme_id

    def get_val(self, obj):
        scheme_id = self.get_real_scheme_id(obj)
        item = models.Device_Item_Value.objects.filter(scheme_id=scheme_id, item_id=obj.id).first()
        serializer = Device_Item_Value_Serializer(instance=item, read_only=True)
        return serializer.data

#    def to_representation(self, obj):
#        ret = super().to_representation(obj)
#        try:
#            val = obj.val.get(scheme_id=obj.scheme_id)
#        except models.Device_Item_Value.DoesNotExist:
#            val = None
#
#        ret['val'] = {
#                'raw_value': normalize_value(val.raw_value) if val else None,
#                'value': normalize_value(val.value) if val else None,
#                }
#        return ret

    class Meta:
        model = models.Device_Item
        fields = ('id', 'name', 'type_id', 'extra', 'group_id', 'device_id', 'parent_id', 'val')

class Plugin_Type_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.Plugin_Type
        fields = '__all__'

class Device_Serializer(serializers.ModelSerializer):
    items = Device_Item_Serializer(many=True, read_only=True)

    class Meta:
        model = models.Device
        fields = ('id', 'name', 'extra', 'plugin_id', 'check_interval', 'items')

class Log_Event_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.Log_Event
        fields = '__all__'

class LDS2_Type(serializers.ModelSerializer):
    class Meta:
        model = models.Device_Item_Type
        fields = ('id','title')

class LDS2_Section(serializers.ModelSerializer):
    class Meta:
        model = models.Section
        fields = ('id','name')

class LDS2_DIG_Type(serializers.ModelSerializer):
    class Meta:
        model = models.DIG_Type
        fields = ('id','title')

class LDS2_Device_Item_Group(serializers.ModelSerializer):
    section = LDS2_Section()
    type = LDS2_DIG_Type()
    class Meta:
        model = models.Device_Item_Group
        fields = ('id','title','section','type')

class LDS2_Device_Item(serializers.ModelSerializer):
    type = LDS2_Type()
    group = LDS2_Device_Item_Group()
    class Meta:
        model = models.Device_Item
        fields = ('id','name','type','group')

class Log_Value_Serializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()
    raw_value = serializers.SerializerMethodField()

    def get_value(self, obj):
        return normalize_value(obj.value)
    
    def get_raw_value(self, obj):
        return normalize_value(obj.raw_value)

    item = LDS2_Device_Item(many=False)

    class Meta:
        model = models.Log_Value
        fields = ('timestamp_msecs', 'item', 'raw_value', 'value', 'user_id')


class Chart_Value_Serializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()
    raw_value = serializers.SerializerMethodField()

    def get_value(self, obj):
        return normalize_value(obj.value)
    
    def get_raw_value(self, obj):
        return normalize_value(obj.raw_value)

    class Meta:
        model = models.Log_Value
        fields = ('timestamp_msecs', 'item_id', 'raw_value', 'value')

class Chart_Param_Serializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    def get_value(self, obj):
        return normalize_value(obj.value)
    
    class Meta:
        model = models.Log_Param
        fields = ('timestamp_msecs', 'group_param_id', 'value')

class Code_Item_Serializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(Code_Item_Serializer, self).__init__(*args, **kwargs)
        if kwargs.get('many', False):
            self.fields.pop('text')

    class Meta:
        model = models.Code_Item
        fields = ('id', 'name', 'text', 'global_id')

