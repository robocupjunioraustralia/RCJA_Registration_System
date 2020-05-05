from django.contrib import admin
from common.admin import *
from coordination.adminPermissions import AdminPermissions

from .models import *

# Register your models here.

@admin.register(CommitteeMember)
class CommitteeMemberAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'userName',
        'userEmail',
        'state',
        'position'
    ]

    autocomplete_fields = [
        'user',
        'state',
    ]
    list_filter = [
        'state',
    ]
    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__email',
        'state__name',
        'state__abbreviation',
        'position',
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'userName',
        'userEmail',
        'state',
        'position',
        'biography',
    ]

    # State based filtering

    @classmethod
    def fieldsToFilterRequest(cls, request):
        from regions.admin import StateAdmin
        from regions.models import State
        return [
            {
                'field': 'state',
                'fieldModel': State,
                'fieldAdmin': StateAdmin,
            }
        ]

    stateFilterLookup = 'state__coordinator'
