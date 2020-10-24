from django.contrib import admin
from django.contrib.admin.models import DELETION
from django.utils.html import format_html
from django.urls import reverse

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

# **********Log Entry**********

from django.contrib.admin.models import LogEntry

@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = [
        '__str__',
        'action_time',
        'user',
        'action_flag',
        'content_type',
    ]
    readonly_fields = [
        'action_time',
        'object_link',
    ]

    list_filter = [
        'action_flag',
        'content_type',
    ]
    search_fields = [
        'object_repr',
        'change_message',
        'user__first_name',
        'user__last_name',
        'user__email',
    ]

    date_hierarchy = 'action_time'

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

    def object_link(self, obj):
        if obj.action_flag == DELETION or obj.content_type is None:
            link = obj.object_repr
        else:
            ct = obj.content_type
            link = format_html(
                '<a href="{}" target="_blank">{}</a>',
                reverse(f'admin:{ct.app_label}_{ct.model}_change', args=[obj.object_id]),
                obj.object_repr,
            )
        return link
    object_link.short_description = 'Object'
