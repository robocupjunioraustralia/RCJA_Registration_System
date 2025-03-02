from django import forms
from django.core.exceptions import ValidationError
from django.utils.functional import lazy

from events.models import Event

def EVENTS_CHOICES():
    for event in Event.objects.all():
        yield (event.pk, event.name)

class OverdueInvoicesForm(forms.Form):
    events = forms.MultipleChoiceField(required=True, widget=forms.CheckboxSelectMultiple,choices=lazy(EVENTS_CHOICES, tuple))