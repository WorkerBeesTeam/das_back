from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from . import models

# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class EmployeeInline(admin.StackedInline):
    model = models.Employee
    can_delete = False
    verbose_name_plural = 'employee'

class UserTeamInline(admin.StackedInline):
    model = models.Team_User
    can_delete = True
    verbose_name_plural = 'teams'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (EmployeeInline,UserTeamInline )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(models.Team)
admin.site.register(models.House)
admin.site.register(models.City)
admin.site.register(models.Company)
