from django.contrib import admin
from common.adminMixins import ExportCSVMixin, FKActionsRemove
from coordination.permissions import AdminPermissions, InlineAdminPermissions, checkCoordinatorPermissionLevel

from .models import State, Region
from events.models import Event, Division, Venue
from schools.models import School

# Register your models here.

class CoordinatorInline(FKActionsRemove, InlineAdminPermissions, admin.TabularInline):
    from coordination.models import Coordinator
    model = Coordinator
    extra = 0
    verbose_name = "Coordinator"
    verbose_name_plural = "Coordinators"
    show_change_link = True
    autocomplete_fields = [
        'user',
    ]

@admin.register(State)
class StateAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        '__str__',
        'abbreviation',
        'typeCompetition',
        'typeUserRegistration',
        'typeGlobal',
        'typeWebsite',
        'bankAccountName',
        'bankAccountBSB',
        'bankAccountNumber',
        'paypalEmail'
    ]
    fieldsets = (
        (None, {
            'fields': ('name', 'abbreviation')
        }),
        ('Type', {
            'fields': ('typeCompetition', 'typeUserRegistration', 'typeGlobal', 'typeWebsite')
        }),
        ('Bank details', {
            'fields': ('bankAccountName', 'bankAccountBSB', 'bankAccountNumber', 'paypalEmail')
        }),
        ('Event details', {
            'fields': (
                ('defaultEventDetails', 'invoiceMessage'),
                ('defaultEventImage', 'defaultEventImageOriginalFilename', 'defaultEventImageFilesize', 'defaultEventImageTag')
            )
        }),
    )
    readonly_fields = [
        'defaultEventImageOriginalFilename',
        'defaultEventImageFilesize',
        'defaultEventImageTag',
    ]
    search_fields = [
        'name',
        'abbreviation'
    ]
    autocomplete_fields = [
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'pk',
        'name',
        'abbreviation',
        'typeCompetition',
        'typeUserRegistration',
        'typeGlobal',
        'typeWebsite',
        'bankAccountName',
        'bankAccountBSB',
        'bankAccountNumber',
        'paypalEmail',
        'defaultEventDetails',
        'invoiceMessage'
    ]
    inlines = [
    ]
    autocompleteFilters = {
        'events/event/': Event,
        'events/division/': Division,
        'events/venue/': Venue,
        'schools/school/': School,
    }

    def get_readonly_fields(self, request, obj):
        readonly_fields = super().get_readonly_fields(request, obj)

        # Don't allow creating new global state if one already exists
        if State.objects.filter(typeGlobal=True).exclude(id=obj.id if obj is not None else None).exists():
            readonly_fields = readonly_fields + ['typeGlobal']

        if obj is None:
            return readonly_fields

        # Restrict changing of type fields
        if not request.user.is_superuser:
            readonly_fields = readonly_fields + ['typeCompetition', 'typeUserRegistration', 'typeGlobal', 'typeWebsite']
        if obj.typeCompetition:
            readonly_fields = readonly_fields + ['typeCompetition']
        if obj.typeUserRegistration:
            readonly_fields = readonly_fields + ['typeUserRegistration']

        return readonly_fields

    def get_inlines(self, request, obj):
        if obj is None:
            return []

        # User must have full permissions to view coordinators
        if checkCoordinatorPermissionLevel(request, obj, ['full']):
            return self.inlines + [
                CoordinatorInline,
            ]

        return self.inlines

    # Filter autocompletes to valid options
    def get_search_results(self, request, queryset, search_term):
        # Filter by typeCompetition
        for url in ['events/event/', 'events/division/', 'events/venue/']:
            if url in request.META.get('HTTP_REFERER', ''):
                queryset = queryset.filter(typeCompetition=True)

        # Filter by typeUserRegistration
        for url in ['users/user/', 'schools/school/', 'regions/region/']:
            if url in request.META.get('HTTP_REFERER', ''):
                queryset = queryset.filter(typeUserRegistration=True)

        # Filter by state for objects that should have full permission level only
        for url in ['users/user/', 'coordination/coordinator/', 'regions/region/']:
            if url in request.META.get('HTTP_REFERER', ''):
                queryset = self.filterQueryset(queryset, request, ['full'], ['full'])

        return super().get_search_results(request, queryset, search_term)

    # State based filtering

    stateFilterLookup = 'coordinator'
    fieldFilteringModel = State

@admin.register(Region)
class RegionAdmin(AdminPermissions, admin.ModelAdmin):
    list_display = [
        'name',
        'state',
        'description',
    ]
    autocomplete_fields = [
        'state',
    ]

    # State based filtering

    fkFilterFields = {
        'state': {
            'stateCoordinatorRequired': True,
            'fieldAdmin': StateAdmin,
        },
    }

    stateFilterLookup = 'state__coordinator'
    globalFilterLookup = 'state'
