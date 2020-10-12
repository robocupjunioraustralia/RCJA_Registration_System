from django.contrib import admin
from common.admin import *

from coordination.adminPermissions import AdminPermissions, InlineAdminPermissions

from .models import *

@admin.register(MentorEventFileType)
class MentorEventFileTypeAdmin(AdminPermissions, admin.ModelAdmin):
    list_display = [
        'name',
        'maxFilesizeMB',
        'allowedFileTypes',
    ]

class EventAvailableFileTypeInline(InlineAdminPermissions, admin.TabularInline):
    model = EventAvailableFileType
    extra = 0

@admin.register(MentorEventFileUpload)
class MentorEventFileUploadAdmin(DifferentAddFieldsMixin, AdminPermissions, admin.ModelAdmin):
    list_display = [
        '__str__',
        'eventAttendance',
        'fileType',
        'event',
        'uploadedBy',
        'filesize',
    ]

    add_readonly_fields = [
    ]
    readonly_fields = [
        'fileUpload',
        'event',
        'uploadedBy',
        'filesize',
        'originalFilename',
    ]

    list_filter = [
        'fileType',
        'eventAttendance__event',
    ]
    search_fields = [
        'fileType__name',
        'uploadedBy__first_name',
        'uploadedBy__last_name',
        'uploadedBy__email',
        'eventAttendance__school__state__name',
        'eventAttendance__school__state__abbreviation',
        'eventAttendance__school__region__name',
        'eventAttendance__school__name',
        'eventAttendance__school__abbreviation',
        'eventAttendance__campus__name',
        'eventAttendance__mentorUser__first_name',
        'eventAttendance__mentorUser__last_name',
        'eventAttendance__mentorUser__email',
        'eventAttendance__event__name',
        'eventAttendance__division__name',
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
