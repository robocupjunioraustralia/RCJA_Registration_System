from django.contrib import admin

from .models import *

# Register your models here.

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = [
        '__str__',
        'abbreviation',
        'treasurerName',
        'bankAccountName',
        'bankAccountBSB',
        'bankAccountNumber',
        'paypalEmail'
        ]

admin.site.register(Region)
