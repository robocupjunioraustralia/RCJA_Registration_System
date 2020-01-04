from django.contrib import admin
from common.admin import *

from .models import *

# Register your models here.

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin, ExportCSVMixin):
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
        'name',
        'abbreviation'
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

@admin.register(Mentor)
class MentorAdmin(admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        '__str__',
        'school',
        'email',
        'mobileNumber'
    ]
    list_filter = [
        'school__state',
        'school__region'
    ]
    search_fields = [
        'school__state__name',
        'school__name',
        'school__abbreviation'
    ]
    autocomplete_fields = [
        'school'
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'firstName',
        'lastName',
        'school',
        'email',
        'mobileNumber'
    ]
