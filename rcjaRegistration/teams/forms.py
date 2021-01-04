from django import forms
from django.core.exceptions import ValidationError

from .models import Student, Team
from events.models import AvailableDivision

from events.forms import BaseEventAttendanceFormInitMixin

import datetime

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['firstName','lastName','yearLevel','gender','birthday']

    birthday = forms.DateField( #coerce type to yyyy-mm-dd so html5 date will prefill correctly
    #this does not affect the display of the field to the user, as that is localised on the clientside
        widget=forms.DateInput(format='%Y-%m-%d'),
        # input_formats=('%Y-%m-%d', )
        )

class TeamForm(BaseEventAttendanceFormInitMixin, forms.ModelForm):
    class Meta:
        model = Team
        fields= ['division', 'campus', 'school', 'event', 'name', 'hardwarePlatform', 'softwarePlatform']

    def __init__(self, *args, user, event, **kwargs):
        super().__init__(*args, user=user, event=event, **kwargs)
        for field in ['hardwarePlatform', 'softwarePlatform']:
            self.fields[field].required = True

    # Validate that this team can be created, not exceeding a school or global team maximum
    def clean(self):
        cleaned_data = super().clean()
        errors = []

        # Only run these validation on team create, allows for a team to be manually created through the admin
        if not self.instance.pk:

            # Get required attributes
            try:
                event = cleaned_data['event']
                division = cleaned_data['division']
                school = cleaned_data['school']
                mentorUser = self.mentorUser
            except KeyError:
                raise ValidationError('Required field is missing')

            # Create dict of attributes to filter teams by
            if school is not None:
                teamFilterDict = {
                    'event': event,
                    'school': school
                }
            else:
                # Independent, filter by mentor
                teamFilterDict = {
                    'event': event,
                    'school': None,
                    'mentorUser': mentorUser
                }

            # Check event based limits 
            if event.event_maxTeamsPerSchool is not None and Team.objects.filter(**teamFilterDict).count() + 1 > event.event_maxTeamsPerSchool:
                errors.append(ValidationError('Max teams for school for this event exceeded. Contact the organiser.'))

            if event.event_maxTeamsForEvent is not None and Team.objects.filter(event=event).count() + 1 > event.event_maxTeamsForEvent:
                errors.append(ValidationError('Max teams for this event exceeded. Contact the organiser.'))

            # Check available division based limits
            try:
                availableDivsion = AvailableDivision.objects.get(division=division, event=event)
            except AvailableDivision.DoesNotExist:
                # This is probably redundant due to the queryset filtering in the init
                raise ValidationError('Team division not valid')

            if availableDivsion.division_maxTeamsPerSchool is not None and Team.objects.filter(**teamFilterDict).filter(division=division).count() + 1 > availableDivsion.division_maxTeamsPerSchool:
                errors.append(ValidationError('Max teams for school for this event division exceeded. Contact the organiser.'))

            if availableDivsion.division_maxTeamsForDivision is not None and Team.objects.filter(event=event, division=division).count() + 1 > availableDivsion.division_maxTeamsForDivision:
                errors.append(ValidationError('Max teams for this event division exceeded. Contact the organiser.'))

        # Raise any errors
        if errors:
            raise ValidationError(errors)

        return cleaned_data
