from django.contrib import admin

# **********Key Value Store**********

import keyvaluestore.admin

# Disable key-value store admin
admin.site.unregister(keyvaluestore.admin.KeyValueStore)

# **********Axes**********

import axes.admin
from axes.admin import AccessLogAdmin as AxesAccessLogAdmin
from axes.admin import AccessAttemptAdmin as AxesAccessAttempAdmin
from axes.models import AccessLog, AccessAttempt

admin.site.unregister(axes.admin.AccessLog)
admin.site.unregister(axes.admin.AccessAttempt)

@admin.register(AccessLog)
class AccessLogAdmin(AxesAccessLogAdmin):
    def has_change_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(AccessAttempt)
class AccessAttempAdmin(AxesAccessAttempAdmin):
    def has_change_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request, obj=None):
        return False

# **********Rest Token**********

from rest_framework.authtoken.admin import TokenAdmin as RestTokenAdmin
from rest_framework.authtoken.models import Token
import rest_framework

admin.site.unregister(rest_framework.authtoken.admin.Token)

@admin.register(Token)
class TokenAdmin(RestTokenAdmin):
    def has_change_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request, obj=None):
        return False

    list_display = ['user', 'created']
