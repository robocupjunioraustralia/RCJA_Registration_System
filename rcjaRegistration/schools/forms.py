from django.db import models
from django.forms import ModelForm
from .models import SchoolAdministrator, School, Campus
from django import forms

class SchoolForm(ModelForm):
    class Meta:
        model = School
        fields = ['name', 'abbreviation', 'state', 'region', 'postcode']

    # Make fields required
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['postcode']:
            self.fields[field].required = True

class SchoolEditForm(SchoolForm):
    addAdministratorEmail = forms.EmailField(required=False)

class CampusForm(ModelForm):
    class Meta:
        model = Campus
        fields = ['name', 'postcode']

    # Make fields required
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['postcode']:
            self.fields[field].required = True

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
