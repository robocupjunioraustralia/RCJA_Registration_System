from django.contrib import admin
from common.adminMixins import ExportCSVMixin, FKActionsRemove
from coordination.permissions import AdminPermissions, InlineAdminPermissions
from django.contrib import messages
from django.forms import Textarea
from django.db import models

from .models import HardwarePlatform, SoftwarePlatform, Team, Student

from events.admin import BaseWorkshopAttendanceAdmin

# Register your models here.

@admin.register(HardwarePlatform)
class HardwarePlatformAdmin(AdminPermissions, admin.ModelAdmin):
    pass

@admin.register(SoftwarePlatform)
class SoftwarePlatformAdmin(AdminPermissions, admin.ModelAdmin):
    pass

class StudentInline(InlineAdminPermissions, admin.TabularInline):
    model = Student
    extra = 0

@admin.register(Team)
class TeamAdmin(BaseWorkshopAttendanceAdmin):
    list_display = [
        'name',
        'event',
        'division',
        'mentorUserName',
        'school',
        'campus',
        'homeState',
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
            'fields': ('hardwarePlatform', 'softwarePlatform', 'notes',)
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
            'fields': ('hardwarePlatform', 'softwarePlatform', 'notes',)
        }),
    )

    inlines = [
        StudentInline
    ]

    search_fields = BaseWorkshopAttendanceAdmin.search_fields + [
        'name',
        'student__firstName',
        'student__lastName',
    ]

    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'pk',
        'name',
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
        'notes',
    ]
    exportFieldsManyRelations = [
        'student_set',
    ]
    autocompleteFilters = {
        'teams/student/': Student,
    }

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
        ('team__event', admin.RelatedOnlyFieldListFilter),
        ('team__division', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        'firstName',
        'lastName',
        'team__name',
        'team__school__state__name',
        'team__school__state__abbreviation',
        'team__school__region__name',
        'team__school__name',
        'team__school__abbreviation',
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

    stateFilterLookup = 'team__event__state__coordinator'
