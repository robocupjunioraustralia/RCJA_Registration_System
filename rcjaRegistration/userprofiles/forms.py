from django.db import models
from django.forms import ModelForm
from .models import Profile
from django import forms
from django.contrib.auth.models import User

class UserEditForm(ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
        ]
    mobileNumber = forms.CharField(max_length=Profile._meta.get_field('mobileNumber').max_length)
