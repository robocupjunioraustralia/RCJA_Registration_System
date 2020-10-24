from django.contrib import admin
from common.adminMixins import ExportCSVMixin, DifferentAddFieldsMixin, FKActionsRemove
from coordination.adminPermissions import AdminPermissions, InlineAdminPermissions
from .adminInlines import SchoolAdministratorInline

from .models import School, Campus, SchoolAdministrator

# Register your models here.

class CampusInline(InlineAdminPermissions, admin.TabularInline):
    model = Campus
    extra = 0

@admin.register(School)
class SchoolAdmin(FKActionsRemove, AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        '__str__',
        'abbreviation',
        'state',
        'region',
        'postcode',
    ]
    list_filter = [
        'state',
        'region'
    ]
    search_fields = [
        'state__name',
        'state__abbreviation',
        'region__name',
        'name',
        'abbreviation',
        'postcode',
    ]
    autocomplete_fields = [
        'state'
    ]
    inlines = [
        CampusInline,
        SchoolAdministratorInline,
    ]
    actions = [
        'export_as_csv',
        'setForceDetailsUpdate',
    ]
    exportFields = [
        'name',
        'abbreviation',
        'state',
        'region',
        'postcode',
    ]

    # Set forceDetailsUpdate if a field is blank
    def save_model(self, request, obj, form, change):
        for field in ['postcode']:
            if getattr(obj, field) is None:
                obj.forceSchoolDetailsUpdate = True
        
        # For existing campuses
        if obj.campus_set.filter(postcode=None).exists():
            obj.forceSchoolDetailsUpdate = True

        super().save_model(request, obj, form, change)

    # For newly added or changed campuses
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if not getattr(instance, 'postcode', True) and not instance.school.forceSchoolDetailsUpdate: # Use true as default because school administrator instances will be included here and have no postcode field
                instance.school.forceSchoolDetailsUpdate = True
                instance.school.save(update_fields=['forceSchoolDetailsUpdate'])

        super().save_formset(request, form, formset, change)

    # State based filtering

    @classmethod
    def fieldsToFilterRequest(cls, request):
        from regions.admin import StateAdmin
        from regions.models import State
        return [
            {
                'field': 'state',
                'fieldModel': State,
                'fieldAdmin': StateAdmin,
            }
        ]

    stateFilterLookup = 'state__coordinator'

    # Actions

    def setForceDetailsUpdate(self, request, queryset):
        queryset.update(forceSchoolDetailsUpdate=True)
    setForceDetailsUpdate.short_description = "Require details update"
    setForceDetailsUpdate.allowed_permissions = ('change',)

@admin.register(Campus)
class CampusAdmin(FKActionsRemove, AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'name',
        'school',
        'postcode',
    ]
    list_filter = [
        'school__state',
        'school__region',
    ]
    search_fields = [
        'name',
        'school__state__name',
        'school__state__abbreviation',
        'school__region__name',
        'school__name',
        'school__abbreviation',
        'postcode',
    ]
    autocomplete_fields = [
        'school'
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'name',
        'school',
        'postcode',
    ]

    # State based filtering

    @classmethod
    def fieldsToFilterRequest(cls, request):
        return [
            {
                'field': 'school',
                'fieldModel': School,
                'fieldAdmin': SchoolAdmin,
            }
        ]

    stateFilterLookup = 'school__state__coordinator'

    fields = [
        'school',
        'name',
        'postcode',
    ]

    # Set forceDetailsUpdate if a field is blank
    def save_model(self, request, obj, form, change):
        if obj.postcode is None:
            obj.school.forceSchoolDetailsUpdate = True
            obj.school.save(update_fields=['forceSchoolDetailsUpdate'])
        
        super().save_model(request, obj, form, change)

    # Don't allow editing school after initial creation
    def get_readonly_fields(self, request, obj=None):
        alwaysReadOnly = []
        if obj:
            return alwaysReadOnly + ['school']
        return alwaysReadOnly

@admin.register(SchoolAdministrator)
class SchoolAdministratorAdmin(FKActionsRemove, DifferentAddFieldsMixin, AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'userName',
        'userEmail',
        'school',
        'campus'
    ]
    list_filter = [
        'school__state',
        'school__region'
    ]
    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__email',
        'school__state__name',
        'school__state__abbreviation',
        'school__region__name',
        'school__name',
        'school__abbreviation',
        'campus__name',
    ]
    autocomplete_fields = [
        'user',
        'school',
        'campus',
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'userName',
        'userEmail',
        'school',
        'campus',
    ]

    add_fields = [
        'school',
        'user',
    ]

    # State based filtering

    @classmethod
    def fieldsToFilterRequest(cls, request):
        return [
            {
                'field': 'school',
                'fieldModel': School,
                'fieldAdmin': SchoolAdmin,
            }
        ]

    @classmethod
    def fieldsToFilterObj(cls, request, obj):
        return [
            {
                'field': 'campus',
                'queryset': Campus.objects.filter(school=obj.school) if obj is not None else Campus.objects.none(),
                'filterNone': True,
            }
        ]

    stateFilterLookup = 'school__state__coordinator'
