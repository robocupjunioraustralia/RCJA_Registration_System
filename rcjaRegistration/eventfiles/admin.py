from django.contrib import admin
from common.adminMixins import ExportCSVMixin, DifferentAddFieldsMixin, FKActionsRemove
from django.utils.html import format_html
from coordination.permissions import AdminPermissions, InlineAdminPermissions
from common.filters import FilteredRelatedOnlyFieldListFilter

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
        'division',
        'uploadedBy',
        'filesize',
    ]

    readonly_fields = [
        'eventAttendance',
        'fileLinkNewTab',
        'event',
        'division',
        'uploadedBy',
        'filesize',
        'originalFilename',
    ]
    exclude = [
        'fileUpload',
    ]

    list_filter = [
        'fileType',
        ('eventAttendance__event', FilteredRelatedOnlyFieldListFilter),
        ('eventAttendance__division', FilteredRelatedOnlyFieldListFilter),
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

    def has_add_permission(self, request, obj=None):
        return False

    # State based filtering

    fkFilterFields = {
        'eventAttendance': {
            'fieldModel': BaseEventAttendance,
            'fieldAdmin': BaseWorkshopAttendanceAdmin,
        },
    }

    statePermissionsFilterLookup = 'eventAttendance__event__state__coordinator'
    filterQuerysetOnSelected = True
    stateSelectedFilterLookup = 'eventAttendance__event__state'
    yearSelectedFilterLookup = 'eventAttendance__event__year'
