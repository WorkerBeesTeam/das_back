import uuid

from django.db import models
from django.contrib.auth.models import User
#from django.conf import settings

class Team(models.Model):
    name = models.CharField(max_length=64)
    def __str__(self):
        return self.name

class Team_User(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

class Employee(models.Model):
    need_to_change_password = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=17, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    daily_report = models.IntegerField(blank=True, null=True, default=None)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, default=None)

class City(models.Model):
    name = models.CharField(max_length=64)
    timezone = models.CharField(max_length=32, default='', blank=True)
    def __str__(self):
        return self.name

class Company(models.Model):
    name = models.CharField(max_length=64)
    def __str__(self):
        return self.name

class House(models.Model):
    parent = models.ForeignKey('self', blank=True, null=True, default=None, on_delete=models.SET_NULL, related_name='children')
    teams = models.ManyToManyField(Team, related_name='in_team')
    city = models.ForeignKey(City, blank=True, null=True, default=None, on_delete=models.SET_NULL)
    company = models.ForeignKey(Company, blank=True, null=True, default=None, on_delete=models.SET_NULL)
    address = models.CharField(max_length=64, default='', blank=True)
    name = models.CharField(max_length=32, unique=True)
    title = models.CharField(max_length=64, default='', blank=True)
    latin_name = models.CharField(max_length=32, unique=True)
    description = models.TextField(default='', blank=True)
    device = models.UUIDField(default=uuid.uuid4)
    lastUsage = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = (
            ( "netherlands", "It's permission for Netherlands" ),
        )

    def __str__(self):
        return '{0} ({1})'.format(self.title, self.name)

    def get_absolute_url(self):
        return '/authors/%s/' % self.id

class EventPool(models.Model):
    date = models.DateTimeField(auto_now_add=True, blank=True)
    
    def __str__(self):
        return self.date.strftime("%d.%m.%y %H:%M") if self.date else 'empty'

class Code(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    name = models.CharField(max_length=64, default='')
    text = models.TextField()

class TelegramSubscriber(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    chat_id = models.IntegerField()

class Distributor(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class Producer(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=100)
    alc = models.CharField(max_length=10)
    ingredients = models.TextField(null=False)
    more_details = models.TextField(null=True, default=None)
    storage_condition = models.CharField(max_length=100)
    pressure = models.FloatField(blank=True, null=True, default=None)
    producer = models.ForeignKey(Producer, null=True, on_delete=models.SET_NULL)
    distributor = models.ForeignKey(Distributor, null=True, on_delete=models.SET_NULL)
    barcode = models.CharField(max_length=100)
    active = models.BooleanField(null=False, default=1)

    class Meta:
        permissions = (
            ( "can_change_brand_bind", "Can change brand bind" ),
        )

    def __str__(self):
        return self.name

