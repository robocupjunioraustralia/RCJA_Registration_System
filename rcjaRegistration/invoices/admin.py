from django.contrib import admin
from common.admin import *
from coordination.adminPermissions import AdminPermissions

from .models import *

# Register your models here.

class InvoicePaymentInline(admin.TabularInline):
    model = InvoicePayment
    extra = 0

@admin.register(Invoice)
class InvoiceAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'event',
        'school',
        'purchaseOrderNumber',
        'invoiceAmount',
        'amountPaid',
        'amountDue'    
    ]
    readonly_fields = [
        'invoiceAmount',
        'amountPaid',
        'amountDue'        
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
        'amountDue'    
    ]

    def stateFilteringAttributes(self, request):
        from coordination.models import Coordinator
        return {
            'event__state__coordinator__in': Coordinator.objects.filter(user=request.user)
        }
    
    # Prevent deleting invoice, because will interfere with auto creation of invoices on team creation
    # Reconsider in conjuction with signals
    def has_delete_permission(self, request, obj=None):
        return False
