from django.contrib import admin
from common.admin import *

from .models import *

# Register your models here.

@admin.register(State)
class StateAdmin(admin.ModelAdmin, ExportCSVMixin):
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        from coordination.models import Coordinator
        qs = qs.filter(coordinator__in = Coordinator.objects.filter(user=request.user))

        return qs

admin.site.register(Region)
