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
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'user',
        'state',
        'position'
    ]
