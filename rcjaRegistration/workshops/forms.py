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
            'birthday',
        ]

    birthday = forms.DateField( #coerce type to yyyy-mm-dd so html5 date will prefill correctly
    #this does not affect the display of the field to the user, as that is localised on the clientside
        widget=forms.DateInput(format='%Y-%m-%d'),
        input_formats=('%Y-%m-%d',),
        required=False,
    )
