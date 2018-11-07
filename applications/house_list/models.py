import uuid

from django.db import models
from django.contrib.auth.models import User
#from django.conf import settings

class Team(models.Model):
    name = models.CharField(max_length=64)
    def __str__(self):
        return self.name

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, default=None)

class House(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    teams = models.ManyToManyField(Team, related_name='in_team')
    name = models.CharField(max_length=32, unique=True)
    title = models.CharField(max_length=64, default='', blank=True)
    latin_name = models.CharField(max_length=32, unique=True)
    description = models.TextField(default='', blank=True)
    device = models.UUIDField(default=uuid.uuid4)
    lastUsage = models.DateTimeField(auto_now=True)

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
