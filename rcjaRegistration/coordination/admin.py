from django.contrib import admin
from common.admin import *
from coordination.adminPermissions import AdminPermissions

from .models import *

# Register your models here.

@admin.register(Coordinator)
class CoordinatorAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'user',
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
        'user',
        'state',
        'permissions',
        'position',
    ]

    # Don't allow editing user after initial creation, because previously selected user's permissions aren't reset
    def get_readonly_fields(self, request, obj=None):
        alwaysReadOnly = []
        if obj:
            return alwaysReadOnly + ['user']
        return alwaysReadOnly

    # State based filtering

    def fieldsToFilter(self, request):
        from regions.models import State
        return [
            {
                'field': 'state',
                'queryset': State.objects.filter(
                    coordinator__user=request.user,
                    coordinator__permissions='full'
                )
            },
        ]

    def stateFilteringAttributes(self, request):
        return {
            'state__coordinator__in': Coordinator.objects.filter(user=request.user),
            'state__coordinator__permissions': 'full',
        }
