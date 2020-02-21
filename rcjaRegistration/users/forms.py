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
        ]

    # def clean(self):
    #     cleaned_data = super().clean()

    #     # Check email is unique because we are setting the username to the email but email uniqueness is not enforced by default
    #     if User.objects.filter(username=cleaned_data.get('email')).exclude(pk=self.instance.pk).exists():
    #         raise forms.ValidationError('There is already an account with this email address.')
