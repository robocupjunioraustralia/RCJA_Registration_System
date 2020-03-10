from django.contrib import admin
from common.admin import *
from coordination.adminPermissions import AdminPermissions, InlineAdminPermissions

from .models import *
from regions.models import State

# Register your models here.

@admin.register(DivisionCategory)
class DivisionCategoryAdmin(AdminPermissions, admin.ModelAdmin):
    pass

@admin.register(Division)
class DivisionAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'name',
        'state',
        'category',
        'description',
    ]
    search_fields = [
        'name',
        'state__name',
        'state__abbreviation',
        'category__name'
    ]
    list_filter = [
        'category',
        'state',
    ]
    actions = [
        'export_as_csv',
    ]
    exportFields = [
        'name',
        'state',
        'category',
        'description',
    ]
    autocomplete_fields = [
        'state',
    ]

    # State based filtering

    @classmethod
    def fieldsToFilterRequest(cls, request):
        from coordination.adminPermissions import reversePermisisons
        return [
            {
                'field': 'state',
                'required': True,
                'queryset': State.objects.filter(
                    coordinator__user=request.user,
                    coordinator__permissions__in=reversePermisisons(Division, ['add', 'change'])
                )
            }
        ]

    @classmethod
    def stateFilteringAttributes(cls, request):
        from coordination.models import Coordinator
        return [
            Q(state__coordinator__in= Coordinator.objects.filter(user=request.user)) | Q(state=None)
        ]

@admin.register(Venue)
class VenueAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'name',
        'state',
        'address',
    ]
    search_fields = [
        'name',
        'state__name',
        'state__abbreviation',
        'address',
    ]
    list_filter = [
        'state',
    ]
    actions = [
        'export_as_csv',
    ]
    exportFields = [
        'name',
        'state',
        'address',
    ]
    autocomplete_fields = [
        'state',
    ]

    # State based filtering

    @classmethod
    def fieldsToFilterRequest(cls, request):
        from coordination.adminPermissions import reversePermisisons
        return [
            {
                'field': 'state',
                'queryset': State.objects.filter(
                    coordinator__user=request.user,
                    coordinator__permissions__in=reversePermisisons(Division, ['add', 'change'])
                )
            }
        ]

    @classmethod
    def stateFilteringAttributes(cls, request):
        from coordination.models import Coordinator
        return {
            'state__coordinator__in': Coordinator.objects.filter(user=request.user)
        }

admin.site.register(Year)

class AvailableDivisionInline(InlineAdminPermissions, admin.TabularInline):
    model = AvailableDivision
    extra = 0
    autocomplete_fields = [
        'division',
    ]

    @classmethod
    def fieldsToFilterRequest(cls, request):
        return [
            {
                'field': 'division',
                'queryset': Division.objects.filter(*DivisionAdmin.stateFilteringAttributes(self, request))
            }
        ]

    @classmethod
    def fieldsToFilterObj(cls, request, obj):
        return [
            {
                'field': 'division',
                'queryset': Division.objects.filter(Q(state=obj.state) | Q(state=None)) if obj is not None else None # Doesn't matter what is returned because haven't set filterNone, so will fall back to fieldsToFilterRequest
            }
        ]


@admin.register(Event)
class EventAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'name',
        'eventType',
        'year',
        'state',
        'startDate',
        'endDate',
        'registrationsOpenDate',
        'registrationsCloseDate',
        'venue',
        'directEnquiriesToName',
    ]
    fieldsets = (
        (None, {
            'fields': ('year', ('state', 'globalEvent'), 'name', 'eventType')
        }),
        ('Dates', {
            'fields': ('startDate', 'endDate', 'registrationsOpenDate', 'registrationsCloseDate')
        }),
        ('Team settings', {
            'fields': ('maxMembersPerTeam', 'event_maxTeamsPerSchool', 'event_maxTeamsForEvent',)
        }),
        ('Billing settings', {
            'fields': ('entryFeeIncludesGST', 'event_billingType', 'event_defaultEntryFee', ('event_specialRateNumber', 'event_specialRateFee'), 'paymentDueDate')
        }),
        ('Details', {
            'fields': ('directEnquiriesTo', 'venue','eventDetails', 'additionalInvoiceMessage')
        }),
    )
    autocomplete_fields = [
        'state',
        'directEnquiriesTo',
        'venue',
    ]
    inlines = [
        AvailableDivisionInline,
    ]
    list_filter = [
        'state',
        'eventType',
        'year',
    ]
    search_fields = [
        'name',
        'state__name',
        'state__abbreviation',
        'directEnquiriesTo__first_name',
        'directEnquiriesTo__last_name',
        'directEnquiriesTo__email',
        'venue__name',
        'venue__address',
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'name',
        'year',
        'state',
        'globalEvent',
        'eventType',
        'startDate',
        'endDate',
        'registrationsOpenDate',
        'registrationsCloseDate',
        'venue',
        'directEnquiriesToName',
        'directEnquiriesToEmail',
        'maxMembersPerTeam',
        'event_maxTeamsPerSchool',
        'event_maxTeamsForEvent',
        'entryFeeIncludesGST',
        'event_billingType',
        'event_defaultEntryFee',
        'event_specialRateNumber',
        'event_specialRateFee',
        'paymentDueDate',
        'eventDetails',
        'additionalInvoiceMessage',
    ]

    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':130})},
    }

    # State based filtering

    @classmethod
    def fieldsToFilterRequest(cls, request):
        from coordination.adminPermissions import reversePermisisons
        from users.models import User
        return [
            {
                'field': 'state',
                'queryset': State.objects.filter(
                    coordinator__user=request.user,
                    coordinator__permissions__in=reversePermisisons(Event, ['add', 'change'])
                )
            },
            # { # See GitHub issue #276
            #     'field': 'directEnquiriesTo',
            #     'queryset': User.objects.filter(
            #         homeState__coordinator__user=request.user,
            #         homeState__coordinator__permissions__in=reversePermisisons(Event, ['add', 'change'])
            #     )
            # },
            {
                'field': 'venue',
                'queryset': Venue.objects.filter(
                    state__coordinator__user=request.user,
                    state__coordinator__permissions__in=reversePermisisons(Event, ['add', 'change'])
                )
            }
        ]

    @classmethod
    def stateFilteringAttributes(cls, request):
        from coordination.models import Coordinator
        return {
            'state__coordinator__in': Coordinator.objects.filter(user=request.user)
        }
