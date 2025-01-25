from django.db import models
from django.forms import ModelForm
from django import forms
from django.core.exceptions import ValidationError


from .models import AssociationMember

class AssociationMemberForm(ModelForm):
    class Meta:
        model = AssociationMember
        fields = [
            'birthday',
            'address',
        ]

    birthday = forms.DateField( #coerce type to yyyy-mm-dd so html5 date will prefill correctly
    #this does not affect the display of the field to the user, as that is localised on the clientside
        widget=forms.DateInput(format='%Y-%m-%d'),
    )
