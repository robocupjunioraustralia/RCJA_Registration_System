from django.contrib import admin
from common.admin import *

from .models import *

# Register your models here.

@admin.register(Coordinator)
class CoordinatorAdmin(admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'user',
        'state',
        'permissions',
        'position'
    ]
    fields = [
        'user',
        'state',
        'permissions',
        'position'
    ]
    autocomplete_fields = [
        'user',
    ]
    list_filter = [
        'state',
        'permissions',
    ]
    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__email',
        'state__name',
        'state__abbreviation',
        'permissions',
        'position',
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'user',
        'state',
        'permissions',
        'position',
    ]

    # Don't allow editing user after initial creation
    def get_readonly_fields(self, request, obj=None):
        alwaysReadOnly = []
        if obj:
            return alwaysReadOnly + ['user']
        return alwaysReadOnly
