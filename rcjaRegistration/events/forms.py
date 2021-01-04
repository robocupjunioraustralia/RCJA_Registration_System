from django import forms

from events.models import Division
from schools.models import Campus

class BaseEventAttendanceFormInitMixin:
    # Override init to filter division and campus, set school and event
    def __init__(self, *args, user, event, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter division to available divisions
        self.fields['division'].queryset = Division.objects.filter(event=event)

        # Filter campus to user's campuses
        self.fields['campus'].queryset = Campus.objects.filter(school=user.currentlySelectedSchool)

        # School field
        self.fields['school'].disabled = True
        self.fields['school'].widget = forms.HiddenInput()
        if user.currentlySelectedSchool:
            self.fields['school'].initial = user.currentlySelectedSchool.id
        else:
            self.fields['school'].initial = None

        # Event field
        self.fields['event'].initial = event.id
        self.fields['event'].disabled = True
        self.fields['event'].widget = forms.HiddenInput()
