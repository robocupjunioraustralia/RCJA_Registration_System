from django.db import models
from django.forms import ModelForm
from .models import SchoolAdministrator, School
from django import forms
from django.contrib.auth.password_validation import validate_password

from users.models import User

class UserSignupForm(ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'mobileNumber',
            'homeState',
            'homeRegion',
        ]
    # Password fields
    password = forms.CharField(widget=forms.PasswordInput)
    passwordConfirm = forms.CharField(widget=forms.PasswordInput)

    # Make fields required
    # Do at form level so can create incomplete users
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['first_name', 'last_name', 'mobileNumber', 'homeState', 'homeRegion']:
            self.fields[field].required = True

    # School fields
    school = forms.ModelChoiceField(queryset=School.objects.all(), label='School')

    def clean(self):
        # Check password
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        passwordConfirm = cleaned_data.get("passwordConfirm")

        if password != passwordConfirm:
            raise forms.ValidationError("Passwords do not match")

        validate_password(password)

class SchoolForm(ModelForm):
    class Meta:
        model = School
        fields = ['name','abbreviation','region','state']
