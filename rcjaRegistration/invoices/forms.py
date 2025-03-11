from django import forms
from django.core.exceptions import ValidationError
from django.utils.functional import lazy

import datetime

from events.models import Event
from coordination.permissions import checkCoordinatorPermission

def EVENTS_CHOICES(request):
    for event in Event.objects.filter(invoice__cache_invoiceAmountInclGST_unrounded__gte=0.05):
        if checkCoordinatorPermission(request, Event, event, 'edit'):
            yield (event.pk, event.name)
        else:
            continue

def getOverdueInvoicesForm(request):
    # Use constructor function as user from request is required for permissions
    class OverdueInvoicesForm(forms.Form):
        events = forms.MultipleChoiceField(required=True, widget=forms.CheckboxSelectMultiple,choices=lazy(lambda: EVENTS_CHOICES(request), tuple))

    return OverdueInvoicesForm(request.POST)