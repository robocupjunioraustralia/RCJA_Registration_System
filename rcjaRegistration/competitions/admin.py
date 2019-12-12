from django.contrib import admin

from .models import *

# Register your models here.

class InvoicePaymentInline(admin.TabularInline):
    model = InvoicePayment
    extra = 0

admin.site.register(State)

admin.site.register(Division)

admin.site.register(Year)

admin.site.register(Competition)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    readonly_fields = [
        'invoiceAmount',
        'amountPaid',
        'amountDue'        
    ]
    inlines = [
        InvoicePaymentInline
    ]