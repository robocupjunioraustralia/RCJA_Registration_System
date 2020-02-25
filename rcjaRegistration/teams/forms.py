from django import forms
from .models import Student, Team
from django.forms import modelformset_factory, inlineformset_factory
from django.core.exceptions import ValidationError
import datetime

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['team','firstName','lastName','yearLevel','gender','birthday']

    birthday = forms.DateField( #coerce type to yyyy-mm-dd so html5 date will prefill correctly
    #this does not affect the display of the field to the user, as that is localised on the clientside
        widget=forms.DateInput(format='%Y-%m-%d'),
        input_formats=('%Y-%m-%d', )
        )
    
class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields= ['division', 'name', 'campus', 'school', 'event']

    # Override init to filter division fk to available divisions
    def __init__(self, *args, user, event, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter division to available divisions
        from events.models import Division
        self.fields['division'].queryset = Division.objects.filter(event=event)

        # Filter campus to user's campuses
        from schools.models import Campus
        self.fields['campus'].queryset = Campus.objects.filter(school=user.currentlySelectedSchool)

        # School field
        self.fields['school'].initial = user.currentlySelectedSchool.id
        self.fields['school'].disabled = True
        self.fields['school'].widget = forms.HiddenInput()

        # Event field
        self.fields['event'].initial = event.id
        self.fields['event'].disabled = True
        self.fields['event'].widget = forms.HiddenInput()
