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
        fields= ['division', 'name', 'campus']

    # Override init to filter division fk to available divisions
    def __init__(self, *args, **kwargs):
        # Pop custom fields before init
        eventID = kwargs.pop('event_id', None)
        user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)

        # Filter division to available divisions
        from events.models import Division
        self.fields['division'].queryset = Division.objects.filter(event=eventID)

        # Filter campus to user's campuses
        from schools.models import Campus
        self.fields['campus'].queryset = Campus.objects.filter(school=user.currentlySelectedSchool)

    StudentFormSet = inlineformset_factory(Team,Student,form=StudentForm) # Is this needed?

    #NOTE: this is a custom clean method to enforce validation on the unique_together constraint
    #This is required because we need to add the event_id manually from the url
    # TODO: Refactor this
    def clean(self): 
        cleaned_data = self.cleaned_data

        teamWithNameInEvent = Team.objects.filter(
            name=cleaned_data['name'],         
            event_id=self.event_id or cleaned_data['event_id']
        )
        
        teamIsSameTeam = False #this case handles editing, when we already have a team
        try:
            if(str(teamWithNameInEvent.first().id) == str(self.team_id)): #team_id must be manually set on the form by the view
                teamIsSameTeam = True
        except AttributeError:
            pass
        if (teamWithNameInEvent.exists() and (not teamIsSameTeam)):
            raise ValidationError(
                'Team with this name already exists for this event'
            )
        
        # Always return cleaned_data
        return cleaned_data
