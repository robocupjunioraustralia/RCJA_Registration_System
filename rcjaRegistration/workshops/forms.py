from django import forms

from .models import WorkshopAttendee

from events.forms import BaseEventAttendanceFormInitMixin

import datetime
    
class WorkshopAttendeeForm(BaseEventAttendanceFormInitMixin, forms.ModelForm):
    class Meta:
        model = WorkshopAttendee
        fields= [
            'division',
            'campus',
            'school',
            'event',
            'firstName',
            'lastName',
            'email',
            'attendeeType',
            'yearLevel',
            'gender',
        ]
