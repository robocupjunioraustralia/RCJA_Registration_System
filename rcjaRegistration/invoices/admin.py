from django.contrib import admin
from common.admin import *
from coordination.adminPermissions import AdminPermissions

from .models import *

# Register your models here.

@admin.register(InvoiceGlobalSettings)
class InvoiceGlobalSettingsAdmin(admin.ModelAdmin):
    # Settings must be present for invoice view to work
    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        if InvoiceGlobalSettings.objects.exists():
            return None
        
        return super().has_add_permission(request)

class InvoicePaymentInline(admin.TabularInline):
    model = InvoicePayment
    extra = 0

@admin.register(Invoice)
class InvoiceAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'invoiceNumber',
        'detailURL',
        'invoiceToUser',
        'event',
        'school',
        'campus',
        'purchaseOrderNumber',
        'invoiceAmountInclGST',
        'amountPaid',
    ]
    readonly_fields = [
        'event',
        'invoiceToUser',
        'school',
        'campus',
        'invoiceNumber',
        'invoiceAmountExclGST',
        'amountGST',
        'invoiceAmountInclGST',
        'amountDueInclGST',
        'amountDuePaypal',
        'amountPaid',     
    ]
    list_filter = [
        'event__state',
        'event',
    ]
    search_fields = [
        'event__state__name',
        'event__state__abbreviation',
        'event__name',
        'school__name',
        'school__abbreviation',
        'campus__name',
        'invoiceToUser__first_name',
        'invoiceToUser__last_name',
        'invoiceToUser__email',
    ]
    inlines = [
        InvoicePaymentInline,
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'event',
        'invoiceToUser',
        'school',
        'campus',
        'invoiceNumber',
        'purchaseOrderNumber',
        'invoiceAmountExclGST',
        'amountGST',
        'invoiceAmountInclGST',
        'amountDueInclGST',
        'amountDuePaypal',
        'amountPaid',
    ]

    def stateFilteringAttributes(self, request):
        from coordination.models import Coordinator
        return {
            'event__state__coordinator__in': Coordinator.objects.filter(user=request.user)
        }

    def detailURL(self, instance):
        from django.utils.safestring import mark_safe
        url = instance.get_absolute_url()  
        return mark_safe(f'<a href="{url}" target="_blank">View invoice</a>')
    detailURL.short_description = 'View invoice'

    # Prevent deleting invoice, because will interfere with auto creation of invoices on team creation
    # Prevent add because always created by signal
    # Reconsider in conjuction with signals
    def has_delete_permission(self, request, obj=None):
        if obj:
            if obj.invoicepayment_set.exists():
                return False
        
        return super().has_delete_permission(request, obj=obj)

    def has_add_permission(self, request, obj=None):
        return False
