from django import forms

from events.models import Division, Year
from schools.models import Campus
from events.models import AvailableDivision

class BaseEventAttendanceFormInitMixin:
    # Override init to filter division and campus, set school and event
    def __init__(self, *args, user, event, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter division to available divisions and check limits not exceeded

        # Filter divisions to maximium not exceeded
        validDivisions = []
        for availableDivision in AvailableDivision.objects.filter(event=event, division__in = self.fields['division'].queryset.values_list('pk', flat=True)):
            if not (availableDivision.maxDivisionRegistrationsForSchoolReached(user) or availableDivision.maxDivisionRegistrationsTotalReached()):
                validDivisions.append(availableDivision.division.id)
        
        # Add current division if existing team - in case override added by coordinator through admin
        if self.instance.pk:
            validDivisions.append(self.instance.division.id)

        self.fields['division'].queryset = Division.objects.filter(event=event, pk__in=validDivisions)

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
        states = [(state.pk, state.name) for state in request.user.adminViewableStates()]
        states.insert(0, ('', '---------'))
        
        years = [(year.year, year.year) for year in Year.objects.all()]

        state = forms.TypedChoiceField(choices=states, coerce=int)
        year = forms.TypedChoiceField(choices=years, coerce=int)

    return SummaryRequestForm(request.GET)

