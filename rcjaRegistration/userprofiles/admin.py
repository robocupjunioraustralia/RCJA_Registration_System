from django.contrib import admin
from common.admin import *
from coordination.adminPermissions import AdminPermissions

from .models import *
from django.contrib.auth.models import User

# Register your models here.

class ProfileInline(admin.StackedInline):
    model = Profile
    extra = 0

    # Profiles are created and deleted through user object
    def has_add_permission(self, request, obj=None):
        return False

    # Currently commented out because blocks user delete because cascade required
    # def has_delete_permission(self, request, obj=None):
    #     return False

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # list_display = [

    # ]
    readonly_fields = [
        'user',
    ]
    fields = [
        'user',
        'mobileNumber'
    ]
    inlines = [
    ]

    # Profiles are created and deleted through user object
    def has_add_permission(self, request, obj=None):
        return False

    # Currently commented out because blocks user delete because cascade required
    # def has_delete_permission(self, request, obj=None):
    #     return False


# User and group admin override

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

admin.site.unregister(Group)

# User admin

admin.site.unregister(User)

@admin.register(User)
class UserAdmin(UserAdmin):
    readonly_fields = UserAdmin.readonly_fields + (
        'user_permissions',
        'groups',
    )
    list_display = UserAdmin.list_display + (
        'is_superuser',
        'is_active',
        'mobileNumber',
    )
    inlines = [ProfileInline]

    def mobileNumber(self, instance):
        return instance.profile.mobileNumber

# UserAdmin.exclude = ()
