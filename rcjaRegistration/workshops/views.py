from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import WorkshopAttendeeForm

from .models import WorkshopAttendee
from events.models import Event

from events.views import CreateEditBaseEventAttendance

import datetime

# Create your views here.

class CreateEditWorkshopAttendee(CreateEditBaseEventAttendance):
    eventType = 'workshop'

    def get(self, request, eventID=None, attendeeID=None):
        if attendeeID is not None:
            attendee = get_object_or_404(WorkshopAttendee, pk=attendeeID)
            event = attendee.event
        else:
            event = get_object_or_404(Event, pk=eventID)
            attendee = None
        self.common(request, event, attendee)

        # Get form
        form = WorkshopAttendeeForm(instance=attendee, user=request.user, event=event)

        return render(request, 'workshops/createEditAttendee.html', {'form': form, 'event':event, 'attendee':attendee})

    def post(self, request, eventID=None, attendeeID=None):
        if attendeeID is not None:
            attendee = get_object_or_404(WorkshopAttendee, pk=attendeeID)
            event = attendee.event
        else:
            event = get_object_or_404(Event, pk=eventID)
            attendee = None
        self.common(request, event, attendee)

        newAttendee = attendee is None

        form = WorkshopAttendeeForm(request.POST, instance=attendee, user=request.user, event=event)

        if form.is_valid():
            # Create attendee object but don't save so can set foreign keys
            attendee = form.save(commit=False)
            attendee.mentorUser = request.user

            # Save attendee
            attendee.save()

            # Redirect if add another in response
            if 'add_text' in request.POST and newAttendee:
                return redirect(reverse('workshops:create', kwargs = {"eventID":event.id}))

            return redirect(reverse('events:details', kwargs = {'eventID':event.id}))

        # Default to displaying the form again if form not valid
        return render(request, 'workshops/createEditAttendee.html', {'form': form, 'event':event, 'attendee':attendee})
