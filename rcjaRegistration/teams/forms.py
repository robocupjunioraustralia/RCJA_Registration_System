from django import forms
from django.core.exceptions import ValidationError

from .models import Team

from events.forms import BaseEventAttendanceFormInitMixin

import datetime

class TeamForm(BaseEventAttendanceFormInitMixin, forms.ModelForm):
    class Meta:
        model = Team
        fields= ['division', 'event', 'name', 'hardwarePlatform', 'softwarePlatform'] #'campus', 'school',

    def __init__(self, *args, user, event, **kwargs):
        super().__init__(*args, user=user, event=event, **kwargs)
        for field in ['hardwarePlatform', 'softwarePlatform']:
            self.fields[field].required = True
