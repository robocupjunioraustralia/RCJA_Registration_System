from django.contrib import admin
from common.adminMixins import ExportCSVMixin, DifferentAddFieldsMixin, FKActionsRemove
from django.utils.html import format_html
from coordination.permissions import AdminPermissions, InlineAdminPermissions

from .models import MentorEventFileType, EventAvailableFileType, MentorEventFileUpload

from events.models import BaseEventAttendance
from events.admin import BaseWorkshopAttendanceAdmin

@admin.register(MentorEventFileType)
class MentorEventFileTypeAdmin(AdminPermissions, admin.ModelAdmin):
    list_display = [
        'name',
        'maxFilesizeMB',
        'allowedFileTypes',
    ]

@admin.register(MentorEventFileUpload)
class MentorEventFileUploadAdmin(FKActionsRemove, AdminPermissions, admin.ModelAdmin):
    list_display = [
        '__str__',
        'eventAttendance',
        'fileType',
        'event',
        'uploadedBy',
        'filesize',
    ]

    readonly_fields = [
        'eventAttendance',
        'fileLinkNewTab',
        'event',
        'uploadedBy',
        'filesize',
        'originalFilename',
    ]
    exclude = [
        'fileUpload',
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

    def fileLinkNewTab(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>', obj.fileUpload.url, obj.originalFilename)
    fileLinkNewTab.short_description = 'File'

    # Add uploadedBy in save
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.uploadedBy = request.user

        super().save_model(request, obj, form, change)

    def has_add_permission(self, request, obj=None):
        return False

    # State based filtering

    fkFilterFields = {
        'eventAttendance': {
            'fieldModel': BaseEventAttendance,
            'fieldAdmin': BaseWorkshopAttendanceAdmin,
        },
    }

    stateFilterLookup = 'eventAttendance__event__state__coordinator'
