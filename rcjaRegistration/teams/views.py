from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory, inlineformset_factory
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import TeamForm, StudentForm

from .models import Student, Team
from events.models import Event

from events.views import CreateEditBaseEventAttendance, eventAttendancePermissions

import datetime

# Create your views here.

@login_required
def details(request, teamID):
    team = get_object_or_404(Team, pk=teamID)

    # Check administrator of this team
    if not eventAttendancePermissions(request, team):
        raise PermissionDenied("You are not an administrator of this team/ attendee")

    return render(request, 'teams/viewTeam.html', {'team':team})

class CreateEditTeam(CreateEditBaseEventAttendance):
    eventType = 'competition'
    def common(self, request, event, team):
        super().common(request, event, team)

        self.StudentInLineFormSet = inlineformset_factory(
            Team,
            Student,
            form = StudentForm,
            extra = 1 if team is None else 0,
            max_num = event.maxMembersPerTeam,
            can_delete = team is not None,
        )

    def get(self, request, eventID=None, teamID=None):
        if teamID is not None:
            team = get_object_or_404(Team, pk=teamID)
            event = team.event
        else:
            event = get_object_or_404(Event, pk=eventID)
            team = None
        self.common(request, event, team)

        # Get form
        form = TeamForm(instance=team, user=request.user, event=event)
        formset = self.StudentInLineFormSet(instance=team)

        return render(request, 'teams/addEditTeam.html', {'form': form, 'formset':formset, 'event':event, 'team':team})

    def post(self, request, eventID=None, teamID=None):
        if teamID is not None:
            team = get_object_or_404(Team, pk=teamID)
            event = team.event
        else:
            event = get_object_or_404(Event, pk=eventID)
            team = None
        self.common(request, event, team)

        newTeam = team is None

        formset = self.StudentInLineFormSet(request.POST, instance=team)
        form = TeamForm(request.POST, instance=team, user=request.user, event=event)
        form.mentorUser = request.user # Needed in form validation to check number of teams for independents not exceeded

        try:
            if form.is_valid() and formset.is_valid():
                # Create team object but don't save so can set foreign keys
                team = form.save(commit=False)
                team.mentorUser = request.user

                # Save team
                team.save()

                # Save student formset
                if newTeam:
                    formset.instance = team
                formset.save()

                # Redirect if add another in response
                if 'add_text' in request.POST and newTeam:
                    return redirect(reverse('teams:create', kwargs = {"eventID":event.id}))

                elif not newTeam:
                    return redirect(reverse('teams:details', kwargs = {"teamID":team.id}))

                return redirect(reverse('events:details', kwargs = {'eventID':event.id}))
        except ValidationError:
            # To catch missing management data
            return HttpResponseBadRequest('Form data missing')

        # Default to displaying the form again if form not valid
        try:
            return render(request, 'teams/addEditTeam.html', {'form': form, 'formset':formset, 'event':event, 'team':team})
        except ValidationError:
            # To catch missing management data
            return HttpResponseBadRequest('Form data missing')

    def delete(self, request, teamID):
        return super().delete(request, teamID)
