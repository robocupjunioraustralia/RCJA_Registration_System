from django.contrib import admin
from common.admin import ExportCSVMixin
from coordination.adminPermissions import AdminPermissions

from .models import Coordinator

# Register your models here.

@admin.register(Coordinator)
class CoordinatorAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'userName',
        'userEmail',
        'state',
        'permissions',
        'position'
    ]
    fields = [
        'user',
        'state',
        'permissions',
        'position'
    ]
    autocomplete_fields = [
        'user',
        'state',
    ]
    list_filter = [
        'state',
        'permissions',
    ]
    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__email',
        'state__name',
        'state__abbreviation',
        'permissions',
        'position',
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'userName',
        'userEmail',
        'state',
        'permissions',
        'position',
    ]

    # State based filtering

    @classmethod
    def fieldsToFilterRequest(cls, request):
        from regions.admin import StateAdmin
        from regions.models import State
        return [
            {
                'field': 'state',
                'required': True,
                'permissions': ['full'],
                'fieldModel': State,
                'fieldAdmin': StateAdmin,
            }
        ]

    stateFilteringPermissions = ['full']
    stateFilterLookup = 'state__coordinator'
