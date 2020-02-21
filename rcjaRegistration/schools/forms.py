from django.db import models
from django.forms import ModelForm
from .models import Mentor, School
from django import forms
from django.contrib.auth.password_validation import validate_password

from users.models import User
from userprofiles.models import Profile

class UserSignupForm(ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
        ]
    # Password fields
    password = forms.CharField(widget=forms.PasswordInput)
    passwordConfirm = forms.CharField(widget=forms.PasswordInput)

    # Profile fields
    mobileNumber = forms.CharField(max_length=Profile._meta.get_field('mobileNumber').max_length)

    # Mentor fields
    school = forms.ModelChoiceField(queryset=School.objects.all(), label='School')

    def clean(self):
        # Check password
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        passwordConfirm = cleaned_data.get("passwordConfirm")

        if password != passwordConfirm:
            raise forms.ValidationError("Passwords do not match")
        
        validate_password(password)

        # Check email is unique because we are setting the username to the email but email uniqueness is not enforced by default
        if User.objects.filter(username=cleaned_data.get('email')).exists():
            raise forms.ValidationError('There is already an account with this email address.')
            
class SchoolForm(ModelForm):
    class Meta:
        model = School
        fields = ['name','abbreviation','region','state']
