import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
#from django.conf import settings

class User(AbstractUser):
    need_to_change_password = models.BooleanField(default=False, blank=True)
    phone_number = models.CharField(max_length=17, blank=True, default='')
    daily_report = models.IntegerField(blank=True, null=True, default=None)

class Scheme_Group(models.Model):
    name = models.CharField(max_length=64)
    def __str__(self):
        return self.name

class Scheme_Group_User(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheme_groups')
    group = models.ForeignKey(Scheme_Group, on_delete=models.CASCADE)
    def __str__(self):
        return self.user.username + ' ' + self.group.name

class City(models.Model):
    name = models.CharField(max_length=64)
    timezone = models.CharField(max_length=32, default='', blank=True)
    def __str__(self):
        return self.name

class Company(models.Model):
    name = models.CharField(max_length=64)
    def __str__(self):
        return self.name

class Scheme(models.Model):
    parent = models.ForeignKey('self', blank=True, null=True, default=None, on_delete=models.SET_NULL, related_name='children')
    groups = models.ManyToManyField(Scheme_Group, related_name='in_group')
    city = models.ForeignKey(City, blank=True, null=True, default=None, on_delete=models.SET_NULL)
    company = models.ForeignKey(Company, blank=True, null=True, default=None, on_delete=models.SET_NULL)
    address = models.CharField(max_length=64, default='', blank=True)
    name = models.CharField(max_length=32, unique=True)
    title = models.CharField(max_length=64, default='', blank=True)
    version = models.CharField(max_length=32, blank=True, default='')
    description = models.TextField(default='', blank=True)
    using_key = models.UUIDField(default=uuid.uuid4)
    last_usage = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = (
            ( "menu_details", "Details menu"),
            ( "menu_management", "Management menu"),
            ( "menu_elements", "Elements menu"),
            ( "menu_log", "Log menu"),
            ( "menu_value_log", "Value log menu"),
            ( "menu_structure", "Structure menu"),
            ( "menu_reports", "Reports menu"),
            ( "menu_wifi_settings", "Wi-Fi settings menu"),
            ( "menu_export", "Export data menu"),
            ( "menu_opening_hours", "Opening hours menu"),
            ( "menu_help", "Help menu"),
        )

    def __str__(self):
        return '{0} ({1})'.format(self.title, self.name)

    def get_absolute_url(self):
        return '/authors/%s/' % self.id

class Code(models.Model):
    group = models.ForeignKey(Scheme_Group, on_delete=models.CASCADE)
    name = models.CharField(max_length=64, default='')
    text = models.TextField()

class Tg_Subscriber(models.Model):
    group = models.ForeignKey(Scheme_Group, on_delete=models.CASCADE)
    chat_id = models.BigIntegerField()

class Tg_User(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, default=None)
    first_name = models.CharField(max_length=64, default='', blank=True)
    last_name = models.CharField(max_length=64, default='', blank=True)
    user_name = models.CharField(max_length=32)
    lang = models.CharField(max_length=16)
    private_chat_id = models.BigIntegerField()

class Tg_Auth(models.Model):
    tg_user = models.OneToOneField(Tg_User, on_delete=models.CASCADE, primary_key=True, related_name='auth')
    expired = models.BigIntegerField()
    token = models.CharField(max_length=512)

# -------------------------------------------------------------

class Schemed_Model(models.Model):
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE)
    class Meta:
        abstract = True

class Titled_Model(Schemed_Model):
    name = models.CharField(max_length=64)
    title = models.CharField(null=True, max_length=64)
    class Meta:
        abstract = True

class Plugin_Type(Schemed_Model):
    name = models.CharField(max_length=128)
    param_names_device = models.CharField(max_length=1024, null=True, default=None)
    param_names_device_item = models.CharField(max_length=1024, null=True, default=None)
    
class Device(Schemed_Model):
    name = models.CharField(max_length=64)
    plugin = models.ForeignKey(Plugin_Type, null=True, default=None, on_delete=models.SET_NULL)
    check_interval = models.IntegerField(default=1500)
    extra = models.TextField(blank=True, null=True, default=None)

# Section is deprecated move to recursive Item_Group
class Section(Schemed_Model):
    name = models.CharField(max_length=64, null=True)
    day_start = models.IntegerField()
    day_end = models.IntegerField()
    
class Code_Item(Schemed_Model):
    name = models.CharField(max_length=2048, default='')
    text = models.TextField()
    global_id = models.IntegerField(null=True, default=None)
    
class DIG_Type(Titled_Model):
    description = models.CharField(max_length=1024, blank=True, default='')

class DIG_Mode(Titled_Model):
    group_type = models.ForeignKey(DIG_Type, null=True, default=None, on_delete=models.SET_NULL)
     
class Device_Item_Group(Schemed_Model):
    def getEquipmentItems(self):
        seen = set()
        items = self.items.filter(type__registerType__in=[Device_Item_Type.RegisterCoils,Device_Item_Type.RegisterHoldingRegisters])
        return [x for x in items if not (x.type_id in seen or seen.add(x.type_id))]
        
    parent = models.ForeignKey('self', blank=True, null=True, default=None, on_delete=models.SET_NULL, related_name='children')
    title = models.CharField(max_length=64, null=True)
    type = models.ForeignKey(DIG_Type, on_delete=models.CASCADE)

    section = models.ForeignKey(Section, related_name='groups', on_delete=models.CASCADE) # deprecated | rename to parent

class DIG_Mode_Item(Schemed_Model):
    group = models.ForeignKey(Device_Item_Group, on_delete=models.CASCADE, related_name='mode')
    mode = models.ForeignKey(DIG_Mode, on_delete=models.SET_NULL, null=True, default=None)

class Sign_Type(Schemed_Model):
    name = models.CharField(max_length=10)

class Save_Timer(Schemed_Model):
    interval = models.IntegerField()

class Device_Item_Type(Titled_Model):
    group_type = models.ForeignKey(DIG_Type, null=True, on_delete=models.SET_NULL)
    sign = models.ForeignKey(Sign_Type, null=True, on_delete=models.SET_NULL)
    
    RT_DISCRETE_INPUTS = 1
    RT_COILS = 2
    RT_INPUT_REGISTERS = 3
    RT_HOLDING_REGISTERS = 4
    RT_FILE = 5
    RT_SIMPLE_BUTTON = 6
    
    Register_Types = (
        (RT_DISCRETE_INPUTS,   'DiscreteInputs'),
        (RT_COILS,             'Coils'),
        (RT_INPUT_REGISTERS,   'InputRegisters'),
        (RT_HOLDING_REGISTERS, 'HoldingRegisters'),
        (RT_FILE,              'File'),
        (RT_SIMPLE_BUTTON,     'SimpleButton'),
    )
    register_type = models.SmallIntegerField(choices=Register_Types, default=RT_INPUT_REGISTERS)
    
    SA_OFF = 1
    SA_IMMEDIATELY = 2
    SA_BY_TIMER = 3
    SA_BY_TIMER_ANY_CASE = 4
    Save_Algorithm = (
        (SA_OFF,     'Off'),
        (SA_IMMEDIATELY,   'Immediately'),
        (SA_BY_TIMER,      'ByTimer'),
        (SA_BY_TIMER_ANY_CASE,      'ByTimerAnyCase'),
    )
    save_algorithm = models.SmallIntegerField(choices=Save_Algorithm, default=SA_OFF)
    save_timer = models.ForeignKey(Save_Timer, null=True, default=None, on_delete=models.SET_NULL)
    
    def __str__(self):
        return self.name

class Device_Item(Schemed_Model):
    parent = models.ForeignKey('self', blank=True, null=True, default=None, on_delete=models.SET_NULL, related_name='children')
    device = models.ForeignKey(Device, related_name='items', on_delete=models.CASCADE)
    group = models.ForeignKey(Device_Item_Group, null=True, related_name='items', on_delete=models.SET_NULL)
    
    name = models.CharField(max_length=64)
    type = models.ForeignKey(Device_Item_Type, on_delete=models.CASCADE)
    extra = models.TextField(blank=True, null=True, default=None)
    
    class Meta:
        permissions = (
            ( "toggle_deviceitem", "Can change device item state" ), # deprecated
        )
 
class Device_Item_Value(Schemed_Model):
    device_item = models.ForeignKey(Device_Item, on_delete=models.CASCADE, related_name='val')
    raw = models.CharField(max_length=512, blank=True, null=True, default=None)
    display = models.CharField(max_length=512, blank=True, null=True, default=None)

    class Meta:
        permissions = (
            ( "toggle_device_item_value", "Can change device item state" ),
        )

class Log_Data(Schemed_Model):
    timestamp_msecs = models.BigIntegerField()
    user_id = models.IntegerField(null=True, default=None)
    item = models.ForeignKey(Device_Item, on_delete=models.CASCADE)
    raw_value = models.CharField(max_length=512, blank=True, null=True, default=None)
    value = models.CharField(max_length=512, blank=True, null=True, default=None)

class Log_Event(Schemed_Model):
    timestamp_msecs = models.BigIntegerField()
    user_id = models.IntegerField(null=True, default=None)
    category = models.CharField(max_length=64)
    text = models.CharField(max_length=1024)
    
    ET_DEBUG = 0
    ET_INFO = 4
    ET_WARNING = 1
    ET_CRITICAL = 2
    ET_FATAL = 3
    ET_USER = 5
    
    Event_Types = (
        (ET_DEBUG,    'Debug'),
        (ET_INFO,     'Info'),
        (ET_WARNING,  'Warning'),
        (ET_CRITICAL, 'Critical'),
        (ET_FATAL,    'Fatal'),
        (ET_USER,     'User'),
    )
    type_id = models.SmallIntegerField(choices=Event_Types, default=ET_INFO)
    
class Settings(Schemed_Model):
    param = models.CharField(max_length=64, primary_key=True)
    value = models.CharField(max_length=64)
    
class DIG_Status_Category(Titled_Model):
    color = models.CharField(max_length=16)
    
class DIG_Status_Type(Schemed_Model):
    group_type = models.ForeignKey(DIG_Type, blank=True, null=True, on_delete=models.SET_NULL)
    category = models.ForeignKey(DIG_Status_Category, null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=64)
    text = models.CharField(max_length=512)
    inform = models.BooleanField(default=True)

class DIG_Status(Schemed_Model):
    group = models.ForeignKey(Device_Item_Group, on_delete=models.CASCADE, related_name='statuses')
    status = models.ForeignKey(DIG_Status_Type, on_delete=models.CASCADE)
    args = models.CharField(max_length=512, null=True, default=None)
     
class DIG_Param_Type(Titled_Model):
    description = models.CharField(max_length=512, blank=True, default='')
    group_type = models.ForeignKey(DIG_Type, null=True, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', blank=True, null=True, default=None, on_delete=models.CASCADE, related_name='children')
#     parent = models.ForeignKey('DIG_Param_Type', null=True, default=None, on_delete=models.CASCADE)
    
    VT_INT = 1
    VT_BOOL = 2
    VT_FLOAT = 3
    VT_STRING = 4
    VT_BYTES = 5
    VT_TIME = 6
    VT_RANGE = 7
    VT_COMBO = 8
    
    Value_Types = (
        (VT_INT,    'Int'),
        (VT_BOOL,   'Bool'),
        (VT_FLOAT,  'Float'),
        (VT_STRING, 'String'),
        (VT_BYTES,  'Bytes'),
        (VT_TIME,   'Time'),
        (VT_RANGE,  'Range'),
        (VT_COMBO,  'Combo'),
    )
    value_type = models.SmallIntegerField(choices=Value_Types, default=VT_BYTES)
    
class DIG_Param(Schemed_Model):
    # parent нужен для того что бы можно было использовать один DIG_Param_Type для многих ParamValue и
    # при этом сделать ParamValue дочерним для другого ParamValue. До этого дочерность определялась DIG_Param_Type::parent_id
    parent = models.ForeignKey('self', blank=True, null=True, default=None, on_delete=models.CASCADE, related_name='childs')
    group = models.ForeignKey(Device_Item_Group, related_name="params", on_delete=models.CASCADE)
    param = models.ForeignKey(DIG_Param_Type, on_delete=models.CASCADE)

class DIG_Param_Value(Schemed_Model):
    group_param = models.ForeignKey(DIG_Param, on_delete=models.CASCADE, related_name='value')
    value = models.TextField(null=True, default=None)
    
class Translation(Schemed_Model):
    lang = models.CharField(max_length=64)
    data = models.TextField()
