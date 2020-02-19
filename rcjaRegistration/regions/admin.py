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
        'defaultCompDetails',
        'invoiceMessage'
    ]

    def stateFilteringAttributes(self, request):
        from coordination.models import Coordinator
        return {
            'coordinator__in': Coordinator.objects.filter(user=request.user)
        }

admin.site.register(Region)
