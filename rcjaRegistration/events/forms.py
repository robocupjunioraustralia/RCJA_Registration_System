from django import forms
from django.core.exceptions import ValidationError
from django.utils.functional import lazy

from events.models import Division, Event
from schools.models import Campus

class BaseEventAttendanceFormInitMixin:
    # Override init to filter division and campus, set school and event
    def __init__(self, *args, user, event, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter division to available divisions
        self.fields['division'].queryset = Division.objects.filter(event=event)

        # Filter campus to user's campuses
        self.fields['campus'].queryset = Campus.objects.filter(school=user.currentlySelectedSchool)

        # School field
        self.fields['school'].disabled = True
        self.fields['school'].widget = forms.HiddenInput()
        if user.currentlySelectedSchool:
            self.fields['school'].initial = user.currentlySelectedSchool.id
        else:
            self.fields['school'].initial = None

        # Event field
        self.fields['event'].initial = event.id
        self.fields['event'].disabled = True
        self.fields['event'].widget = forms.HiddenInput()

def COMPETITIONS_CHOICES():
    for event in Event.objects.filter(status='published', eventType='competition'):
        yield (event.pk, event.name)

def WORKSHOPS_CHOICES():
    for event in Event.objects.filter(status='published', eventType='workshop'):
        yield (event.pk, event.name)

class AdminEventsForm(forms.Form):
    competitions = forms.MultipleChoiceField(required=False, widget=forms.CheckboxSelectMultiple,choices=lazy(COMPETITIONS_CHOICES, tuple))
    workshops = forms.MultipleChoiceField(required=False, widget=forms.CheckboxSelectMultiple,choices=lazy(WORKSHOPS_CHOICES, tuple))

    def clean(self):
        workshops = len(self.cleaned_data['workshops'])>0
        competitions = len(self.cleaned_data['competitions'])>0
        if workshops and competitions:
            raise ValidationError("Cannot directly compare workshops and competitions")
