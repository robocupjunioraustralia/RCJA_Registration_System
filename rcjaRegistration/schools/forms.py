from django.db import models
from django.forms import ModelForm
from .models import SchoolAdministrator, School, Campus
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
    school = forms.ModelChoiceField(queryset=School.objects.filter(schooladministrator__isnull=True, team__isnull=True), label='School', required=False)

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

    addAdministratorEmail = forms.EmailField(required=False)

class CampusForm(ModelForm):
    class Meta:
        model = Campus
        fields = ['name']

class SchoolAdministratorForm(ModelForm):
    class Meta:
        model = SchoolAdministrator
        fields = ['user', 'campus']

    # Override init to filter campus fk
    def __init__(self, *args, **kwargs):
        # Pop custom fields before init
        user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)

        # Filter campus to user's campuses
        from schools.models import Campus
        self.fields['campus'].queryset = Campus.objects.filter(school=user.currentlySelectedSchool)

        # Make user not editable to prevent user field form being enumerated in drop down
        self.fields['user'].disabled = True
        # This is needed because even if disabled all of the options are available in the html
        # This works to prevent a data leak but it is not the best way of achieving this
        from users.models import User
        self.fields['user'].queryset = User.objects.filter(schooladministrator__school=user.currentlySelectedSchool)
