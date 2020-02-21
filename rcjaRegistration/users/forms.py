from django.db import models
from django.forms import ModelForm
from django import forms
from users.models import User

class UserEditForm(ModelForm):
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
