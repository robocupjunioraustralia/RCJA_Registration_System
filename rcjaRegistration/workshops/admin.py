from django.contrib import admin
from common.admin import *
from coordination.adminPermissions import AdminPermissions
from django.contrib import messages

from .models import *

from events.admin import BaseWorkshopAttendanceAdmin

# Register your models here.

@admin.register(WorkshopAttendee)
class WorkshopAttendeeAdmin(BaseWorkshopAttendanceAdmin):
    list_display = [
        'attendeeFullName',
        'event',
        'division',
        'mentorUserName',
        'school',
        'campus',
        'homeState',
    ]
    fieldsets = (
        ('Event', {
            'fields': ('event', 'division')
        }),
        ('School', {
            'fields': ('mentorUser', 'school', 'campus',)
        }),
        ('Required details', {
            'fields': ('attendeeType', 'firstName', 'lastName')
        }),
        ('Optional details', {
            'fields': ('email',)
        }),
        ('Required details for students', {
            'fields': ('yearLevel', 'gender', 'birthday')
        }),
    )
    add_fieldsets = (
        ('Event', {
            'fields': ('event', 'division')
        }),
        ('School', {
            'description': "Select this team's mentor.<br>If they are a mentor for one school that school will be autofilled. If they are mentor of more than one school you will need to select the school. Leave school blank if independent.<br>You can select campus after you have clicked save.",
            'fields': ('mentorUser', 'school',)
        }),
        ('Required details', {
            'fields': ('attendeeType', 'firstName', 'lastName')
        }),
        ('Optional details', {
            'fields': ('email',)
        }),
        ('Required details for students', {
            'fields': ('yearLevel', 'gender', 'birthday')
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
        'firstName',
        'lastName',
        'event',
        'division',
        'mentorUserName',
        'mentorUserEmail',
        'school',
        'campus',
        'homeState',
    ]
