from django.contrib import admin

from .models import *

# Register your models here.

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
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

@admin.register(Mentor)
class MentorAdmin(admin.ModelAdmin):
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
