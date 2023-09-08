from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory, inlineformset_factory
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.urls import reverse

from .forms import TeamForm, StudentForm

import datetime

from .models import Student, Team
from events.models import Event

from events.views import CreateEditBaseEventAttendance, mentorEventAttendanceAccessPermissions

# Create your views here.

@login_required
def details(request, teamID):
    team = get_object_or_404(Team, pk=teamID)

    # Check event is published
    if not team.event.published():
        raise PermissionDenied("Event is not published")

    # Check administrator of this team
    if not mentorEventAttendanceAccessPermissions(request, team):
        raise PermissionDenied("You are not an administrator of this team/ attendee")

    context = {
        "team": team,
        "students": team.student_set.all(),
        'uploadedFiles': team.mentoreventfileupload_set.all(),
    }

    return render(request, 'teams/details.html', context)

class CreateEditTeam(CreateEditBaseEventAttendance):
    eventType = 'competition'
    def common(self, request, event, team):
        super().common(request, event, team)

        if not team:
            if event.maxEventTeamsForSchoolReached(request.user):
                raise PermissionDenied("Max teams for school for this event reached. Contact the organiser if you want to register more teams for this event.")

            if event.maxEventTeamsTotalReached():
                raise PermissionDenied("Max teams for this event reached. Contact the organiser if you want to register more teams for this event.")

        self.StudentInLineFormSet = inlineformset_factory(
            Team,
            Student,
            form = StudentForm,
            min_num = 1,
            extra = 0,
            max_num = event.maxMembersPerTeam,
            can_delete = team is not None,
            validate_max = True,
            validate_min = True,
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

        return render(request, 'teams/createEditTeam.html', {'form': form, 'formset':formset, 'event':event, 'team':team})

    def post(self, request, eventID=None, teamID=None):
        if teamID is not None:
            team = get_object_or_404(Team, pk=teamID)
            event = team.event
        else:
            event = get_object_or_404(Event, pk=eventID)
            team = None
        self.common(request, event, team)

        newTeam = team is None

        formset = self.StudentInLineFormSet(request.POST, instance=team, error_messages={"missing_management_form": "ManagementForm data is missing or has been tampered with"})
        form = TeamForm(request.POST, instance=team, user=request.user, event=event)

        if all([x.is_valid() for x in (form, formset)]):
            # Create team object but don't save so can set foreign keys
            team = form.save(commit=False)
            team.mentorUser = request.user

            # Save team
            team.save()

            # Save student formset
            if newTeam:
                # This is needed because it is possible to create teams and add students in one request
                formset.instance = team
            formset.save()

            # Redirect if add another in response
            if 'add_text' in request.POST and newTeam:
                return redirect(reverse('teams:create', kwargs = {"eventID":event.id}))

            elif not newTeam:
                return redirect(reverse('teams:details', kwargs = {"teamID":team.id}))

            return redirect(reverse('events:details', kwargs = {'eventID':event.id}))

        return render(request, 'teams/createEditTeam.html', {'form': form, 'formset':formset, 'event':event, 'team':team})

