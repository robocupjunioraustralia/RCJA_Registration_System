from django.contrib import admin
from coordination.permissions import AdminPermissions
from django.contrib import messages

from .models import WorkshopAttendee

from events.admin import BaseWorkshopAttendanceAdmin

# Register your models here.

@admin.register(WorkshopAttendee)
class WorkshopAttendeeAdmin(BaseWorkshopAttendanceAdmin):
    list_display = [
        'attendeeFullName',
        'attendeeType',
        'event',
        'division',
        'creationDateTime',
        'homeState',
    ]
    fieldsets = (
        ('Event', {
            'fields': ('event', 'division')
        }),
        ('Required details', {
            'fields': ('attendeeType', 'firstName', 'lastName', 'yearLevel', 'gender')
        }),
        ('Required details for teachers', {
            'fields': ('email',)
        }),
        ('Advanced billing settings', {
            'description': "By default an invoice will be created for paid events. Selecting an invoice override will remove this attendee from that invoice and add it to a different invoice, which can be for a different school or mentor.",
            'fields': ('invoiceOverride', )
        }),
    )
    add_fieldsets = (
        ('Event', {
            'fields': ('event', 'division')
        }),
        ('Required details', {
            'fields': ('attendeeType', 'firstName', 'lastName', 'yearLevel', 'gender')
        }),
        ('Required details for teachers', {
            'fields': ('email',)
        }),
    )

    search_fields = BaseWorkshopAttendanceAdmin.search_fields + [
        'firstName',
        'lastName',
        'email',
    ]

    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'pk',
        'firstName',
        'lastName',
        'email',
        'attendeeType',
        'yearLevel',
        'gender',
        'event',
        'division',
        'creationDateTime',
        'homeState',
        'homeRegion',
        'invoiceOverride',
    ]
    exportFieldsManyRelations = [
        'mentor_questionresponse_set',
    ]

    eventTypeMapping = 'workshop'
