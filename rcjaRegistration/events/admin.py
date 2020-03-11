from django.contrib import admin
from common.admin import *
from coordination.adminPermissions import AdminPermissions, InlineAdminPermissions
from django.contrib import messages

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
    def fieldsToFilterObj(cls, request, obj):
        return [
            {
                'field': 'division',
                'queryset': Division.objects.filter(Q(state=obj.state) | Q(state=None)) if obj is not None else Division.objects.none(), # Inline not displayed on create so will never fallback to None
                'filterNone': True
            }
        ]

@admin.register(Event)
class EventAdmin(DifferentAddFieldsMixin, AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
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
            'fields': ('directEnquiriesTo', 'venue', 'eventDetails', 'additionalInvoiceMessage')
        }),
    )
    add_fieldsets = (
        (None, {
            'fields': ('year', ('state', 'globalEvent'), 'name', 'eventType')
        }),
        ('Dates', {
            'fields': ('startDate', 'endDate', 'registrationsOpenDate', 'registrationsCloseDate')
        }),
        ('Team settings', {
            'description': "More options will be available after you click save",
            'fields': ('maxMembersPerTeam',)
        }),
        ('Billing settings', {
            'description': "More options will be available after you click save",
            'fields': ('entryFeeIncludesGST', 'event_billingType', 'event_defaultEntryFee')
        }),
        ('Details', {
            'description': "More options will be available after you click save",
            'fields': ('directEnquiriesTo',)
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
    add_inlines = [ # Don't include available divisions here so the divisions will be fitlered when shown
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

    # Message user during save
    def save_model(self, request, obj, form, change):
        if obj.pk:
            if obj.venue is None:
                self.message_user(request, f"{obj}: You haven't added a venue yet, we recommend adding a venue.", messages.WARNING)
        
        super().save_model(request, obj, form, change)

    # Message user regarding divisions during inline save
    def save_formset(self, request, form, formset, change):
        # Don't want to display error on add page because inlines not shown so impossible to add divisions
        if change:
            if len(formset.cleaned_data) == 0:
                self.message_user(request, f"{form.instance}: You haven't added any divisions yet, people won't be able to register.", messages.WARNING)

        super().save_formset(request, form, formset, change)

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
        ]

    @classmethod
    def stateFilteringAttributes(cls, request):
        from coordination.models import Coordinator
        return {
            'state__coordinator__in': Coordinator.objects.filter(user=request.user)
        }

    @classmethod
    def fieldsToFilterObj(cls, request, obj):
        return [
            {
                'field': 'venue',
                'queryset': Venue.objects.filter(state=obj.state) if obj is not None else Venue.objects.none(), # Field not displayed on create so will never fallback to None
                'filterNone': True
            }
        ]
