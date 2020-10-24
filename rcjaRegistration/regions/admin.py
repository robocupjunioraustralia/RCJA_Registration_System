from django.contrib import admin
from common.adminMixins import ExportCSVMixin, FKActionsRemove
from coordination.adminPermissions import AdminPermissions, InlineAdminPermissions, checkStatePermissionsLevels

from .models import State, Region

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
        'typeRegistration',
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
            'fields': ('typeRegistration', 'typeGlobal', 'typeWebsite')
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
        'name',
        'abbreviation',
        'typeRegistration',
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

    def get_readonly_fields(self, request, obj):
        readonly_fields = super().get_readonly_fields(request, obj)

        # Don't allow creating new global state if one already exists
        if State.objects.filter(typeGlobal=True).exclude(id=obj.id if obj is not None else None).exists():
            readonly_fields = readonly_fields + ['typeGlobal']

        if obj is None:
            return readonly_fields

        # Restrict changing of type fields
        if not request.user.is_superuser:
            readonly_fields = readonly_fields + ['typeRegistration', 'typeGlobal', 'typeWebsite']
        elif obj.typeRegistration:
            readonly_fields = readonly_fields + ['typeRegistration', 'typeGlobal']
        elif obj.typeGlobal:
            readonly_fields = readonly_fields + ['typeRegistration']

        return readonly_fields

    def get_inlines(self, request, obj):
        if obj is None:
            return []

        # User must have full permissions to view coordinators
        if checkStatePermissionsLevels(request, obj, ['full']):
            return self.inlines + [
                CoordinatorInline,
            ]

        return self.inlines

    # Filter autocompletes to valid options
    def get_search_results(self, request, queryset, search_term):
        # Filter by typeRegistration
        for url in ['users/user/', 'events/event/', 'events/division/', 'events/venue/', 'schools/school/']:
            if url in request.META.get('HTTP_REFERER', ''):
                queryset = queryset.filter(typeRegistration=True)

        # Filter by state
        from coordination.adminPermissions import reversePermisisons
        for url in ['users/user/', 'coordination/coordinator/']:
            if url in request.META.get('HTTP_REFERER', ''):
                queryset = self.filterQuerysetByState(queryset, request, ['full'])

        from events.models import Event, Division, Venue
        from schools.models import School
        urlPairs = {
            'events/event/': Event,
            'events/division/': Division,
            'events/venue/': Venue,
            'schools/school/': School,
        }

        for url in urlPairs:
            if url in request.META.get('HTTP_REFERER', ''):
                permissionLevels = reversePermisisons(urlPairs[url], ['add', 'change'])
                queryset = self.filterQuerysetByState(queryset, request, permissionLevels)

        return super().get_search_results(request, queryset, search_term)

    # State based filtering

    stateFilterLookup = 'coordinator'

@admin.register(Region)
class RegionAdmin(AdminPermissions, admin.ModelAdmin):
    list_display = [
        'name',
        'description',
    ]
