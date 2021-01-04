from django.contrib import admin
from common.adminMixins import ExportCSVMixin, FKActionsRemove
from coordination.adminPermissions import AdminPermissions

from .models import Coordinator
from regions.admin import StateAdmin

# Register your models here.

@admin.register(Coordinator)
class CoordinatorAdmin(FKActionsRemove, AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'userName',
        'userEmail',
        'state',
        'permissionLevel',
        'position'
    ]
    fields = [
        'user',
        'state',
        'permissionLevel',
        'position'
    ]
    autocomplete_fields = [
        'user',
        'state',
    ]
    list_filter = [
        'state',
        'permissionLevel',
    ]
    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__email',
        'state__name',
        'state__abbreviation',
        'permissionLevel',
        'position',
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'pk',
        'userName',
        'userEmail',
        'state',
        'permissionLevel',
        'position',
    ]

    # State based filtering

    @classmethod
    def fieldsToFilterRequest(cls, request):
        return [
            {
                'field': 'state',
                'required': True,
                'permissionLevels': ['full'],
                'fieldAdmin': StateAdmin,
            }
        ]

    stateFilteringPermissions = ['full']
    stateFilterLookup = 'state__coordinator'
