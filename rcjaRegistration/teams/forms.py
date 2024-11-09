from django import forms
from django.core.exceptions import ValidationError

from .models import Student, Team
from events.models import AvailableDivision

from events.forms import BaseEventAttendanceFormInitMixin

import datetime

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['firstName','lastName','yearLevel','gender']

class TeamForm(BaseEventAttendanceFormInitMixin, forms.ModelForm):
    class Meta:
        model = Team
        fields= ['division', 'campus', 'school', 'event', 'name', 'hardwarePlatform', 'softwarePlatform']

    def __init__(self, *args, user, event, **kwargs):
        super().__init__(*args, user=user, event=event, **kwargs)
        for field in ['hardwarePlatform', 'softwarePlatform']:
            self.fields[field].required = True

        # Filter divisions to maximium not exceeded
        validDivisions = []
        for availableDivision in AvailableDivision.objects.filter(event=event, division__in = self.fields['division'].queryset.values_list('pk', flat=True)):
            if not (availableDivision.maxDivisionTeamsForSchoolReached(user) or availableDivision.maxDivisionTeamsTotalReached()):
                validDivisions.append(availableDivision.division.id)
        
        # Add current division if existing team - in case override added by coordinator through admin
        if self.instance.pk:
            validDivisions.append(self.instance.division.id)

        self.fields['division'].queryset = self.fields['division'].queryset.filter(pk__in=validDivisions)
