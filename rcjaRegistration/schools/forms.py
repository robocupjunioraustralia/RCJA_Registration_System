from django.db import models
from django.forms import ModelForm
from .models import Mentor, School
from django import forms
class MentorForm(ModelForm):
    class Meta:
        model = Mentor
        fields = ['school', 'mobileNumber','firstName','lastName','email',]
    password = forms.CharField(widget=forms.PasswordInput)
    passwordConfirm = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super(MentorForm, self).clean()
        password = cleaned_data.get("password")
        passwordConfirm = cleaned_data.get("passwordConfirm")

        if password != passwordConfirm:
            raise forms.ValidationError(
                "Passwords do not match"
            )
class MentorEditForm(MentorForm):
        class Meta:
            model = Mentor
            fields = ['mobileNumber','firstName','lastName','email',]
            
class SchoolForm(ModelForm):
    class Meta:
        model = School
        fields = ['name','abbreviation','region','state']