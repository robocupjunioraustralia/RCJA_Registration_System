from django.db import models
from django.forms import ModelForm
from .models import Profile
from django import forms
from django.contrib.auth.models import User

class ProfileEditForm(ModelForm):
    class Meta:
        model = Profile
        fields = [
            'mobileNumber',
        ]
    
    first_name = forms.CharField(max_length=User._meta.get_field('first_name').max_length)
    last_name = forms.CharField(max_length=User._meta.get_field('last_name').max_length)
    email = forms.EmailField()
