from django.contrib import admin
from common.admin import *
from coordination.adminPermissions import AdminPermissions
from .adminInlines import SchoolAdministratorInline

from .models import *

# Register your models here.

class CampusInline(admin.TabularInline):
    model = Campus
    extra = 0

@admin.register(School)
class SchoolAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        '__str__',
        'abbreviation',
        'state',
        'region'
    ]
    list_filter = [
        'state',
        'region'
    ]
    search_fields = [
        'state__name',
        'state__abbreviation',
        'region__name',
        'name',
        'abbreviation',
    ]
    autocomplete_fields = [
        'state'
    ]
    inlines = [
        CampusInline,
        SchoolAdministratorInline,
    ]
    actions = [
        'export_as_csv',
        'setForceDetailsUpdate',
    ]
    exportFields = [
        'name',
        'abbreviation',
        'state',
        'region'
    ]

    # State based filtering

    @classmethod
    def fieldsToFilterRequest(cls, request):
        from coordination.adminPermissions import reversePermisisons
        from regions.models import State
        return [
            {
                'field': 'state',
                'queryset': State.objects.filter(
                    coordinator__user=request.user,
                    coordinator__permissions__in=reversePermisisons(School, ['add', 'change'])
                )
            }
        ]

    @classmethod
    def stateFilteringAttributes(cls, request):
        from coordination.models import Coordinator
        return {
            'state__coordinator__in': Coordinator.objects.filter(user=request.user)
        }

    def setForceDetailsUpdate(self, request, queryset):
        queryset.update(forceSchoolDetailsUpdate=True)
    setForceDetailsUpdate.short_description = "Require details update"
    setForceDetailsUpdate.allowed_permissions = ('change',)

@admin.register(Campus)
class CampusAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'name',
        'school',
    ]
    list_filter = [
        'school__state',
        'school__region',
    ]
    search_fields = [
        'name',
        'school__state__name',
        'school__state__abbreviation',
        'school__region__name',
        'school__name',
        'school__abbreviation',
    ]
    autocomplete_fields = [
        'school'
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'name',
        'school',
    ]

    # State based filtering

    @classmethod
    def fieldsToFilterRequest(cls, request):
        from coordination.adminPermissions import reversePermisisons
        return [
            {
                'field': 'school',
                'queryset': School.objects.filter(
                    state__coordinator__user=request.user,
                    state__coordinator__permissions__in=reversePermisisons(Campus, ['add', 'change'])
                )
            }
        ]

    @classmethod
    def stateFilteringAttributes(cls, request):
        from coordination.models import Coordinator
        return {
            'school__state__coordinator__in': Coordinator.objects.filter(user=request.user)
        }

    fields = [
        'school',
        'name',
    ]

    # Don't allow editing school after initial creation
    def get_readonly_fields(self, request, obj=None):
        alwaysReadOnly = []
        if obj:
            return alwaysReadOnly + ['school']
        return alwaysReadOnly

@admin.register(SchoolAdministrator)
class SchoolAdministratorAdmin(DifferentAddFieldsMixin, AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'userName',
        'userEmail',
        'school',
        'campus'
    ]
    list_filter = [
        'school__state',
        'school__region'
    ]
    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__email',
        'school__state__name',
        'school__state__abbreviation',
        'school__region__name',
        'school__name',
        'school__abbreviation',
        'campus__name',
    ]
    autocomplete_fields = [
        'user',
        'school',
        'campus',
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'userName',
        'userEmail',
        'school',
        'campus',
    ]

    add_fields = [
        'school',
        'user',
    ]

    # State based filtering

    @classmethod
    def fieldsToFilterRequest(cls, request):
        from coordination.adminPermissions import reversePermisisons
        from users.models import User
        return [
            {
                'field': 'school',
                'queryset': School.objects.filter(
                    state__coordinator__user=request.user,
                    state__coordinator__permissions__in=reversePermisisons(SchoolAdministrator, ['add', 'change'])
                )
            },
        ]

    @classmethod
    def fieldsToFilterObj(cls, request, obj):
        return [
            {
                'field': 'campus',
                'queryset': Campus.objects.filter(school=obj.school) if obj is not None else Campus.objects.none(),
                'filterNone': True,
            }
        ]

    @classmethod
    def stateFilteringAttributes(cls, request):
        from coordination.models import Coordinator
        return {
            'school__state__coordinator__in': Coordinator.objects.filter(user=request.user)
        }
