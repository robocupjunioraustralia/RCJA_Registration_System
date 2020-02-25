from django.contrib import admin
from common.admin import *
from coordination.adminPermissions import AdminPermissions

from .models import *

# Register your models here.


@admin.register(Division)
class DivisionAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'name',
        'description'
    ]
    search_fields = [
        'name'
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'name',
        'description'
    ]

admin.site.register(Year)

class AvailableDivisionInline(admin.TabularInline):
    model = AvailableDivision
    extra = 0

@admin.register(Event)
class EventAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'name',
        'year',
        'state',
        'startDate',
        'endDate',
        'registrationsOpenDate',
        'registrationsCloseDate',
        'directEnquiriesTo'
    ]
    readonly_fields = [
    ]
    fieldsets = (
        (None, {
            'fields': ('year', 'state', 'name', 'eventType')
        }),
        ('Dates', {
            'fields': ('startDate', 'endDate', 'registrationsOpenDate', 'registrationsCloseDate')
        }),
        ('Team settings', {
            'fields': ('event_maxMembersPerTeam', 'event_maxTeamsPerSchool', 'event_maxTeamsForEvent',)
        }),
        ('Billing settings', {
            'fields': ('event_billingType', 'event_defaultEntryFee', ('event_specialRateNumber', 'event_specialRateFee'))
        }),
        ('Details', {
            'fields': ('directEnquiriesTo', 'eventDetails', 'location', 'additionalInvoiceMessage')
        }),
    )
    inlines = [
        AvailableDivisionInline,
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
        'directEnquiriesTo'
    ]

    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':130})},
    }

    def stateFilteringAttributes(self, request):
        from coordination.models import Coordinator
        return {
            'state__coordinator__in': Coordinator.objects.filter(user=request.user)
        }
