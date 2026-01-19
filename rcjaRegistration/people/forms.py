from django import forms
from django.core.exceptions import ValidationError

from schools.models import SchoolAdministrator
from .models import Student

from events.forms import BaseEventAttendanceFormInitMixin

import datetime

class NewStudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['firstName','lastName','yearLevel','gender']
