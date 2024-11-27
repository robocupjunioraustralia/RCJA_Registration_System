from django import forms
from datetime import datetime

from events.models import Division, Year
from regions.models import State
from schools.models import Campus

from coordination.permissions import checkCoordinatorPermission

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

def getSummaryForm(request):
    # Use constructor function as user from request is required for permissions
    class SummaryRequestForm(forms.Form):
        states = []
        for i, state in enumerate(State.objects.all()):
            if checkCoordinatorPermission(request, State, state, 'view'):            
                states.append((str(i),state.name))

        years = []
        for i, year in enumerate(Year.objects.all()):
            years.append((year.year,year.year))
        
        state = forms.ChoiceField(choices=states)
        year = forms.TypedChoiceField(choices=years, initial=datetime.now().year)

    return SummaryRequestForm(request.GET)

