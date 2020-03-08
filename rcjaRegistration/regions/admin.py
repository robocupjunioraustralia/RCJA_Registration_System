from django.contrib import admin
from common.admin import *
from coordination.adminPermissions import AdminPermissions

from .models import *

# Register your models here.

@admin.register(State)
class StateAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        '__str__',
        'abbreviation',
        'treasurerName',
        'bankAccountName',
        'bankAccountBSB',
        'bankAccountNumber',
        'paypalEmail'
    ]
    search_fields = [
        'name',
        'abbreviation'
    ]
    autocomplete_fields = [
        'treasurer',
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'name',
        'abbreviation',
        'treasurerName',
        'bankAccountName',
        'bankAccountBSB',
        'bankAccountNumber',
        'paypalEmail',
        'defaultEventDetails',
        'invoiceMessage'
    ]

    # State based filtering

    def fieldsToFilter(self, request):
        from coordination.adminPermissions import reversePermisisons
        from users.models import User
        return [
            {
                'field': 'treasurer',
                'queryset': User.objects.filter(
                    homeState__coordinator__user=request.user,
                    homeState__coordinator__permissions__in=reversePermisisons(State, ['change'])
                )
            }
        ]

    def stateFilteringAttributes(self, request):
        from coordination.models import Coordinator
        return {
            'coordinator__in': Coordinator.objects.filter(user=request.user)
        }

@admin.register(Region)
class RegionAdmin(AdminPermissions, admin.ModelAdmin):
    list_display = [
        'name',
        'description',
    ]
