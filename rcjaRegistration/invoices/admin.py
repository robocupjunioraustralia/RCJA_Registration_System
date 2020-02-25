from django.contrib import admin
from common.admin import *
from coordination.adminPermissions import AdminPermissions

from .models import *

# Register your models here.

@admin.register(InvoiceGlobalSettings)
class InvoiceGlobalSettingsAdmin(admin.ModelAdmin):
    pass

class InvoicePaymentInline(admin.TabularInline):
    model = InvoicePayment
    extra = 0

@admin.register(Invoice)
class InvoiceAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'event',
        'invoiceToUser',
        'school',
        'campus',
        'invoiceNumber',
        'purchaseOrderNumber',
        'invoiceAmount',
        'amountPaid',
        'amountDueInclGST'    
    ]
    readonly_fields = [
        'event',
        'invoiceToUser',
        'school',
        'campus',
        'invoiceNumber',
        'invoiceAmount',
        'amountPaid',
        'amountDueInclGST'        
    ]
    list_filter = [
        'event__state',
        'event'
    ]
    search_fields = [
        'event__state__name',
        'event__name',
        'school__name',
        'school__abbreviation'
    ]
    inlines = [
        InvoicePaymentInline
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'event',
        'school',
        'purchaseOrderNumber',
        'invoiceAmount',
        'amountPaid',
        'amountDueInclGST'    
    ]

    def stateFilteringAttributes(self, request):
        from coordination.models import Coordinator
        return {
            'event__state__coordinator__in': Coordinator.objects.filter(user=request.user)
        }
    
    # Prevent deleting invoice, because will interfere with auto creation of invoices on team creation
    # Prevent add because always created by signal
    # Reconsider in conjuction with signals
    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False
