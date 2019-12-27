from django.db import models
from django.forms import ModelForm
from .models import Mentor, School
from django import forms
class MentorForm(ModelForm):
    class Meta:
        model = Mentor
        fields = ['school', 'mobileNumber','firstName','lastName','email','mobileNumber']
    password = forms.CharField(widget=forms.PasswordInput)
    passwordConfirm = forms.CharField(widget=forms.PasswordInput)
class SchoolForm(ModelForm):
    class Meta:
        model = School
        fields = ['name','abbreviation','region','state']