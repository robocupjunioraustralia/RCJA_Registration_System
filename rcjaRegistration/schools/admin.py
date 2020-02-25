from django.contrib import admin
from common.admin import *
from coordination.adminPermissions import AdminPermissions

from .models import *

# Register your models here.

class SchoolAdministratorInline(admin.TabularInline):
    model = SchoolAdministrator
    extra = 0
    verbose_name = "Administrator"
    verbose_name_plural = "Administrators"
    # Define fields to define order
    fields = [
        'user',
        'campus',
    ]
    autocomplete_fields = [
        'user',
        'campus',
    ]

class CampusInline(admin.TabularInline):
    model = Campus
    extra = 0

@admin.register(School)
class SchoolAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        '__str__',
        'abbreviation',
        'state',
        'region'
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
    ]
    autocomplete_fields = [
        'state'
    ]
    inlines = [
        CampusInline,
        SchoolAdministratorInline,
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'name',
        'abbreviation',
        'state',
        'region'
    ]

    def stateFilteringAttributes(self, request):
        from coordination.models import Coordinator
        return {
            'state__coordinator__in': Coordinator.objects.filter(user=request.user)
        }

@admin.register(Campus)
class CampusAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'name',
        'school',
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
    ]

    def stateFilteringAttributes(self, request):
        from coordination.models import Coordinator
        return {
            'school__state__coordinator__in': Coordinator.objects.filter(user=request.user)
        }

@admin.register(SchoolAdministrator)
class SchoolAdministratorAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'user',
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
        'user',
        'school',
        'campus',
    ]

    def stateFilteringAttributes(self, request):
        from coordination.models import Coordinator
        return {
            'school__state__coordinator__in': Coordinator.objects.filter(user=request.user)
        }
