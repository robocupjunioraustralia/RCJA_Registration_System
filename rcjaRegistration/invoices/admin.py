from django.contrib import admin
from common.adminMixins import ExportCSVMixin
from coordination.permissions import AdminPermissions, InlineAdminPermissions, checkCoordinatorPermission
from django.utils.html import format_html, escape
from django.contrib import messages
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from common.filters import FilteredRelatedOnlyFieldListFilter
from django.db.models import Sum, F, Q

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

class AmountDueFilter(admin.SimpleListFilter):
    title = "Amount Due"
    parameter_name = "amountDueStatus"

    def lookups(self, request, model_admin):
        return [("True","Fully Paid"), ("False",'Unpaid')]

    def queryset(self, request, queryset):
        if self.value() == "True":
            return queryset.filter(_amoundDueFilter__lt=0.05)
        elif self.value() == "False":
            return queryset.filter(Q(_amoundDueFilter__gte=0.05) | Q(_amoundDueFilter__isnull=True))
        return queryset

class InvoiceAmountFilter(admin.SimpleListFilter):
    title = "Invoice Amount"
    parameter_name = "invoiceAmountStatus"

    def lookups(self, request, model_admin):
        return [
            ('all', 'All'),
            (None, "Non Zero"),
            ("empty", "Zero"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "empty":
            return queryset.filter(cache_invoiceAmountInclGST_unrounded__lt=0.05)
        elif self.value() == "all":
            return queryset
        return queryset.filter(cache_invoiceAmountInclGST_unrounded__gte=0.05)

    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': changelist.get_query_string({self.parameter_name: lookup,}, []),
                'display': title,
            }

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
        'amountDueInclGST',
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
        AmountDueFilter,
        InvoiceAmountFilter,
        ('event__state', admin.RelatedOnlyFieldListFilter),
        ('event', FilteredRelatedOnlyFieldListFilter),
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
        'pk',
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        qs = qs.prefetch_related('school', 'invoiceToUser')
        qs = qs.annotate(_sumPayments=Sum('invoicepayment__amountPaid'))
        qs = qs.annotate(_amoundDueFilter=F('cache_invoiceAmountInclGST_unrounded') - F('_sumPayments'))

        return qs

    def markPaidToday(self, request, queryset):
        def addErrorMessage(errorMessage, message):
            # Helper function to update error message while avoiding duplicate errors
            if message not in errorMessage:
                errorMessage = errorMessage + f" {message}"
        
            return errorMessage

        # Messaging variables
        errorMessage = ""
        numberUpdated = 0

        # Need to loop over the queryset to use function logic - invoiceAmount is not available on queryset
        # Also to provide object level permissions
        for invoice in queryset:
            # Check has permission to edit this invoice
            if not checkCoordinatorPermission(request, Invoice, invoice, 'change'):
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
            paymentObj = invoice.invoicepayment_set.create(amountPaid=invoice.invoiceAmountInclGST(), datePaid=datetime.datetime.today().date())
            numberUpdated += 1

            # Log the action
            LogEntry.objects.log_action(
                user_id = request.user.id,
                content_type_id = ContentType.objects.get_for_model(Invoice).pk,
                object_id = invoice.id,
                object_repr = str(invoice),
                action_flag = CHANGE,
                change_message = '[{{"added": {{"name": "Payment", "object": "{}"}}}}]'.format(paymentObj)
            )

        # Message user with result
        self.message_user(request, f"{numberUpdated} invoices marked as paid.{errorMessage}", messages.INFO)

    markPaidToday.short_description = "Mark paid today"
    markPaidToday.allowed_permissions = ('change',)

    statePermissionsFilterLookup = 'event__state__coordinator'

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

    filterQuerysetOnSelected = True
    stateSelectedFilterLookup = 'event__state'
    yearSelectedFilterLookup = 'event__year'
