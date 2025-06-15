from django.contrib import admin
from common.adminMixins import ExportCSVMixin, FKActionsRemove
from coordination.permissions import AdminPermissions, InlineAdminPermissions
from django.contrib import messages
from django.forms import Textarea
from django.db import models
from common.filters import FilteredRelatedOnlyFieldListFilter
from django.utils.html import format_html
from django.urls import reverse

from .models import PlatformCategory, HardwarePlatform, SoftwarePlatform, Team, Student

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

class StudentInline(InlineAdminPermissions, admin.TabularInline):
    model = Student
    extra = 0
    min_num = 1

@admin.register(Team)
class TeamAdmin(BaseWorkshopAttendanceAdmin):
    list_display = [
        'name',
        'event',
        'division',
        'creationDateTime',
        'mentorUserName',
        'school',
        'campus',
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
        ('School', {
            'fields': ('mentorUser', 'school', 'campus',)
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
        ('School', {
            'description': "Select this team's mentor.<br>If they are a mentor for one school that school will be autofilled. If they are mentor of more than one school you will need to select the school. Leave school blank if independent.<br>You can select campus after you have clicked save.",
            'fields': ('mentorUser', 'school',)
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
        StudentInline
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
        'mentorUserName',
        'mentorUserEmail',
        'mentorUserPK',
        'school',
        'campus',
        'homeState',
        'homeRegion',
        'schoolPostcode',
        'hardwarePlatform',
        'softwarePlatform',
        'invoiceOverride',
    ]
    exportFieldsManyRelations = [
        'mentor_questionresponse_set',
        'student_set',
    ]
    autocompleteFilters = {
        'teams/student/': Student,
    }

    def uploadFileURL(self, obj):
        return format_html('<a href="{}" target="_blank">Upload file -></a>', reverse('eventfiles:uploadFile', args=(obj.id, )))
    uploadFileURL.short_description = 'Upload file'

    eventTypeMapping = 'competition'

    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows':2, 'cols':40})},
    }

    # State based filtering

    fieldFilteringModel = Team

@admin.register(Student)
class StudentAdmin(FKActionsRemove, AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        '__str__',
        'team',
    ]
    autocomplete_fields = [
        'team',
    ]
    list_filter = [
        ('team__event', FilteredRelatedOnlyFieldListFilter),
        ('team__division', FilteredRelatedOnlyFieldListFilter),
    ]
    search_fields = [
        'firstName',
        'lastName',
        'team__name',
        'team__school__state__name',
        'team__school__state__abbreviation',
        'team__school__region__name',
        'team__school__name',
        'team__campus__name',
        'team__mentorUser__first_name',
        'team__mentorUser__last_name',
        'team__mentorUser__email',
        'team__event__name',
        'team__division__name',
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'pk',
        'team',
        'teamPK',
        'firstName',
        'lastName',
        'yearLevel',
        'gender',
    ]

    # State based filtering

    fkFilterFields = {
        'team': {
            'fieldAdmin': TeamAdmin,
        },
    }

    statePermissionsFilterLookup = 'team__event__state__coordinator'
    filterQuerysetOnSelected = True
    stateSelectedFilterLookup = 'team__event__state'
    yearSelectedFilterLookup = 'team__event__year'
