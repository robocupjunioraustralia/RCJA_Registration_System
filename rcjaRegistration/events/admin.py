from django.contrib import admin
from common.admin import *

from .models import *

# Register your models here.

class InvoicePaymentInline(admin.TabularInline):
    model = InvoicePayment
    extra = 0


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'name',
        'state',
        'description'
    ]
    list_filter = [
        'state'
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'name',
        'state',
        'description'
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        from coordination.models import Coordinator
        qs = qs.filter(Q(state__coordinator__in = Coordinator.objects.filter(user=request.user)) | Q(state=None))

        return qs

admin.site.register(Year)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'name',
        'year',
        'state',
        'startDate',
        'endDate',
        'registrationsOpenDate',
        'registrationsCloseDate',
        'entryFee',
        'directEnquiriesTo'
    ]
    list_filter = [
        'state',
        'year'
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'name',
        'year',
        'state',
        'startDate',
        'endDate',
        'registrationsOpenDate',
        'registrationsCloseDate',
        'entryFee',
        'directEnquiriesTo'
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        from coordination.models import Coordinator
        qs = qs.filter(state__coordinator__in = Coordinator.objects.filter(user=request.user))

        return qs

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin, ExportCSVMixin):
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        from coordination.models import Coordinator
        qs = qs.filter(event__state__coordinator__in = Coordinator.objects.filter(user=request.user))

        return qs
