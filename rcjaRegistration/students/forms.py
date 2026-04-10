from django import forms
from django.core.exceptions import ValidationError

from schools.models import SchoolAdministrator
from .models import Student

from events.forms import BaseEventAttendanceFormInitMixin

import datetime


class NewStudentForm(forms.ModelForm):

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    class Meta:
        model = Student
        fields = ["firstName", "lastName", "graduationYear", "gender"]

    def clean(self):
        cleaned_data = super().clean()
        firstName = cleaned_data.get("firstName")
        lastName = cleaned_data.get("lastName")
        graduationYear = cleaned_data.get("graduationYear")
        gender = cleaned_data.get("gender")

        exists = Student.objects.filter(
            mentorUser=self.user,
            school=self.user.currentlySelectedSchool,
            graduationYear=graduationYear,
            firstName=firstName,
            lastName=lastName,
            gender=gender,
        ).exists()
        if exists:
            raise ValidationError("Student already registered.")
        self.instance.mentorUser = self.user
        self.instance.school = self.user.currentlySelectedSchool
        return cleaned_data
