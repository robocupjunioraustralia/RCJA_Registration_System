from django.contrib import admin
from common.adminMixins import ExportCSVMixin, FKActionsRemove
from coordination.permissions import AdminPermissions, InlineAdminPermissions
from django.contrib import messages
from django.forms import Textarea
from django.db import models
from common.filters import FilteredRelatedOnlyFieldListFilter
from django.utils.html import format_html
from django.urls import reverse

from .models import PlatformCategory, HardwarePlatform, SoftwarePlatform, Team,TeamParticipation
from events.admin import BaseWorkshopAttendanceAdmin

# Register your models here.

@admin.register(PlatformCategory)
class PlatformCategoryAdmin(AdminPermissions, admin.ModelAdmin):
    pass

@admin.register(HardwarePlatform)
class HardwarePlatformAdmin(AdminPermissions, admin.ModelAdmin):
    list_display = [
        'name',
        'category',
    ]
    list_filter = [
        'category',
    ]

@admin.register(SoftwarePlatform)
class SoftwarePlatformAdmin(AdminPermissions, admin.ModelAdmin):
    list_display = [
        'name',
        'category',
    ]
    list_filter = [
        'category',
    ]

class ParticipationInline(InlineAdminPermissions, admin.TabularInline):
    model = TeamParticipation
    extra = 0
    min_num = 1

@admin.register(Team)
class TeamAdmin(BaseWorkshopAttendanceAdmin):
    list_display = [
        'name',
        'event',
        'division',
        'creationDateTime',
        'homeState',
        'withdrawn',
        'uploadFileURL',
    ]
    fieldsets = (
        (None, {
            'fields': ('name',)
        }),
        ('Event', {
            'fields': ('event', 'division')
        }),
        ('Details', {
            'fields': (
                'hardwarePlatform',
                'softwarePlatform',
                'creationDateTime',
                'updatedDateTime',
                'withdrawn',
            )
        }),
        ('Advanced billing settings', {
            'description': "By default an invoice will be created for paid events. Selecting an invoice override will remove this team from that invoice and add it to a different invoice, which can be for a different school or mentor.",
            'fields': ('invoiceOverride', )
        }),
    )
    add_fieldsets = (
        (None, {
            'fields': ('name',)
        }),
        ('Event', {
            'fields': ('event', 'division')
        }),
        ('Details', {
            'fields': ('hardwarePlatform', 'softwarePlatform',)
        }),
    )

    readonly_fields = [
        'creationDateTime',
        'updatedDateTime',
    ]

    inlines = [
        ParticipationInline
    ]

    search_fields = BaseWorkshopAttendanceAdmin.search_fields + [
        'name',
        'student__firstName',
        'student__lastName',
    ]

    list_filter = BaseWorkshopAttendanceAdmin.list_filter + [
        'hardwarePlatform',
        'softwarePlatform',
    ]

    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'creationDateTime',
        'updatedDateTime',
        'pk',
        'name',
        'withdrawn',
        'event',
        'division',
        'homeState',
        'homeRegion',
        'hardwarePlatform',
        'softwarePlatform',
        'invoiceOverride',
    ]
    exportFieldsManyRelations = [
        'student_set',
    ]
    """
    autocompleteFilters = {
        'teams/student/': StudentA,
    }"""

    def uploadFileURL(self, obj):
        return format_html('<a href="{}" target="_blank">Upload file -></a>', reverse('eventfiles:uploadFile', args=(obj.id, )))
    uploadFileURL.short_description = 'Upload file'

    eventTypeMapping = 'competition'

    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows':2, 'cols':40})},
    }

    # State based filtering

    fieldFilteringModel = Team

