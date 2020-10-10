from django.contrib import admin
from common.admin import *

from coordination.adminPermissions import AdminPermissions, InlineAdminPermissions

from .models import *


@admin.register(MentorEventFileUpload)
class MentorEventFileUploadAdmin(DifferentAddFieldsMixin, AdminPermissions, admin.ModelAdmin):
    list_display = [
        '__str__',
        'eventAttendance',
        'event',
        'uploadedBy',
    ]

    add_readonly_fields = [
    ]
    readonly_fields = [
        'fileUpload',
        'event',
        'uploadedBy',
        'filesize',
    ]

    autocomplete_fields = [
    ]

    list_filter = [
    ]
    search_fields = [
    ]


    # Add uploadedBy in save
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.uploadedBy = request.user

        super().save_model(request, obj, form, change)


    # def has_change_permission(self, request, obj=None):
    #     return False
    # def has_add_permission(self, request, obj=None):
    #     return False

    # State based filtering

    @classmethod
    def fieldsToFilterRequest(cls, request):
        from events.admin import BaseWorkshopAttendanceAdmin
        from events.models import BaseEventAttendance
        return [
            {
                'field': 'eventAttendance',
                'fieldModel': BaseEventAttendance,
                'fieldAdmin': BaseWorkshopAttendanceAdmin,
            }
        ]

    stateFilterLookup = 'eventAttendance__event__state__coordinator'
