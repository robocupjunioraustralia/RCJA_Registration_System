from django.contrib import admin
from common.admin import *
from coordination.adminPermissions import AdminPermissions

from .models import *

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
        from regions.models import State
        from users.models import User
        return [
            {
                'field': 'state',
                'queryset': State.objects.filter(
                    coordinator__user=request.user,
                    coordinator__permissions='full'
                )
            },
        ]

    @classmethod
    def stateFilteringAttributes(cls, request):
        return {
            'state__coordinator__in': Coordinator.objects.filter(user=request.user),
            'state__coordinator__permissions': 'full',
        }
