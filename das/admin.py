from django.apps import apps
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as Base_User_Admin
# from django.contrib.auth.models import User

from . import models

# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton

class User_Scheme_Group_Inline(admin.StackedInline):
    model = models.Scheme_Group_User
    can_delete = True
    verbose_name_plural = 'teams'

# Define a new User admin
class User_Admin(Base_User_Admin):
    inlines = (User_Scheme_Group_Inline, )

# Re-register UserAdmin
# admin.site.unregister(User)
admin.site.register(models.User, User_Admin)

admin.site.register(models.Scheme_Group)
admin.site.register(models.Scheme)
admin.site.register(models.City)
admin.site.register(models.Company)
admin.site.register(models.Disabled_Param)
admin.site.register(models.Disabled_Status)

## all other models
# models = apps.get_models()
# 
# for model in models:
#     try:
#         admin.site.register(model)
#     except admin.sites.AlreadyRegistered:
#         pass

