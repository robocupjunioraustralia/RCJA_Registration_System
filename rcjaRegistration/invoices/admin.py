from django.contrib import admin
from common.adminMixins import ExportCSVMixin
from coordination.adminPermissions import AdminPermissions, InlineAdminPermissions, checkStatePermissions
from django.utils.html import format_html, escape
from django.contrib import messages

import datetime

from .models import InvoiceGlobalSettings, Invoice, InvoicePayment

# Register your models here.

@admin.register(InvoiceGlobalSettings)
class InvoiceGlobalSettingsAdmin(admin.ModelAdmin):
    # Settings must be present for invoice view to work
    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        if InvoiceGlobalSettings.objects.exists():
            return False
        
        return super().has_add_permission(request)

class InvoicePaymentInline(InlineAdminPermissions, admin.TabularInline):
    model = InvoicePayment
    extra = 0

@admin.register(Invoice)
class InvoiceAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'invoiceNumber',
        'detailURL',
        'invoiceToUserName',
        'event',
        'school',
        'campus',
        'purchaseOrderNumber',
        'invoiceAmountInclGST',
        'amountPaid',
    ]
    readonly_fields = [
        'event',
        'invoiceToUserName',
        'invoiceToUserEmail',
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
        'export_as_csv',
        'markPaidToday',
    ]
    exportFields = [
        'event',
        'invoiceToUserName',
        'invoiceToUserEmail',
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

    def markPaidToday(self, request, queryset):
        def addErrorMessage(errorMessage, message):
            if message not in errorMessage:
                errorMessage = errorMessage + f" {message}"
        
            return errorMessage

        errorMessage = ""
        numberUpdated = 0

        for invoice in queryset:
            # Check has permission to edit this invoice
            if not checkStatePermissions(request, invoice, 'change'):
                errorMessage = addErrorMessage(errorMessage, "Couldn't update some invoices as didn't have permission.")
                continue

            # Skip invoices that already have a full or partial payment
            if invoice.invoicepayment_set.exists():
                errorMessage = addErrorMessage(errorMessage, "Couldn't update some invoices as already a payment.")
                continue

            # Skip blank invoices
            if invoice.invoiceAmountInclGST() < 0.05: # Rounded because consistent with what user sees and not used in subsequent calculations
                errorMessage = addErrorMessage(errorMessage, "Skipped some blank invoices.")
                continue

            # Create invoice payment for this invoice, use rounded amount because this is what is displayed in the interface, not being used in further calculations
            invoice.invoicepayment_set.create(amountPaid=invoice.invoiceAmountInclGST(), datePaid=datetime.datetime.today().date())
            numberUpdated += 1

        self.message_user(request, f"{numberUpdated} invoices marked as paid.{errorMessage}", messages.INFO)

    markPaidToday.short_description = "Mark paid today"
    markPaidToday.allowed_permissions = ('change',)

    stateFilterLookup = 'event__state__coordinator'

    def detailURL(self, instance):
        return format_html('<a href="{}" target="_blank">View invoice</a>', instance.get_absolute_url())
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
