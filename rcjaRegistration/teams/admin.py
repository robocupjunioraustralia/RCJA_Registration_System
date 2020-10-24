from django.contrib import admin
from common.adminMixins import ExportCSVMixin, FKActionsRemove
from coordination.adminPermissions import AdminPermissions, InlineAdminPermissions
from django.contrib import messages

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
            'fields': ('hardwarePlatform', 'softwarePlatform',)
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
        'name',
        'event',
        'division',
        'mentorUserName',
        'mentorUserEmail',
        'school',
        'campus',
        'homeState',
        'hardwarePlatform',
        'softwarePlatform',
    ]

    eventTypeMapping = 'competition'

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
        'team__event',
        'team__division',
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
        'team',
        'firstName',
        'lastName',
        'yearLevel',
        'gender',
        'birthday',
    ]

    # State based filtering

    @classmethod
    def fieldsToFilterRequest(cls, request):
        return [
            {
                'field': 'team',
                'fieldModel': Team,
                'fieldAdmin': TeamAdmin,
            }
        ]

    stateFilterLookup = 'team__event__state__coordinator'
