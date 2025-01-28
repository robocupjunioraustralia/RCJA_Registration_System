from django import forms
from django.core.exceptions import ValidationError

from .models import Student, Team

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
