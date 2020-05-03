from django.contrib import admin
from common.admin import *
from coordination.adminPermissions import AdminPermissions

from .models import *

# Register your models here.

class CoordinatorInline(admin.TabularInline):
    from coordination.models import Coordinator
    model = Coordinator
    extra = 0
    verbose_name = "State coordinator"
    verbose_name_plural = "State Coordinators"
    show_change_link = True
    autocomplete_fields = [
        'user',
    ]

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
        'treasurerEmail',
        'bankAccountName',
        'bankAccountBSB',
        'bankAccountNumber',
        'paypalEmail',
        'defaultEventDetails',
        'invoiceMessage'
    ]
    inlines = [
    ]

    def get_inlines(self, request, obj):
        if obj is None:
            return []

        # User must have full permissions to view coordinators
        if self.checkStatePermissionsLevels(request, obj, ['full']):
            return self.inlines + [
                CoordinatorInline,
            ]
        return self.inlines

    # State based filtering

    stateFilterLookup = 'coordinator'

@admin.register(Region)
class RegionAdmin(AdminPermissions, admin.ModelAdmin):
    list_display = [
        'name',
        'description',
    ]
