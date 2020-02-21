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
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'user',
        'state',
        'position'
    ]

    # Don't allow editing user after initial creation
    def get_readonly_fields(self, request, obj=None):
        alwaysReadOnly = []
        if obj:
            return alwaysReadOnly + ['user']
        return alwaysReadOnly
