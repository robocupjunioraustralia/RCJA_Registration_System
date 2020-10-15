from django.db import models
from django.forms import ModelForm
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from users.models import User

class UserForm(ModelForm):
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

    # Make fields required
    # Do at form level so can create incomplete users
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['first_name', 'last_name', 'mobileNumber', 'homeState', 'homeRegion']:
            self.fields[field].required = True

class UserSignupForm(UserForm):
    # Password fields
    password = forms.CharField(widget=forms.PasswordInput)
    passwordConfirm = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        # Check password
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        passwordConfirm = cleaned_data.get("passwordConfirm")

        if password != passwordConfirm:
            raise forms.ValidationError("Passwords do not match")

        if not password:
            raise forms.ValidationError("Password must not be blank")

        validate_password(password)
