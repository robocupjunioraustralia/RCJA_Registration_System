from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory, inlineformset_factory
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.urls import reverse

from .forms import TeamForm, StudentForm

import datetime

from .models import Student, Team
from events.models import Event, AvailableDivision

from events.views import CreateEditBaseEventAttendance, mentorEventAttendanceAccessPermissions, getDivisionsMaxReachedWarnings, getAvailableToCopyTeams

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
    def common(self, request, event, team, sourceTeam=None):
        super().common(request, event, team)

        if sourceTeam:
            # Check source team permissions
            if not mentorEventAttendanceAccessPermissions(request, sourceTeam):
                raise PermissionDenied("You are not an administrator of this team.")

            # Check not already copied
            if Team.objects.filter(event=event, copiedFrom=sourceTeam):
                raise PermissionDenied("Team already copied to this event.")

            # Check not from the current event
            if sourceTeam.event == event:
                raise PermissionDenied("Team source event can't be same as destination event.")

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

    def get(self, request, eventID=None, teamID=None, sourceTeamID=None):
        sourceTeam = None
        event = None
        team = None
        if sourceTeamID is not None:
            sourceTeam = get_object_or_404(Team, pk=sourceTeamID)
            event = get_object_or_404(Event, pk=eventID)
        elif teamID is not None:
            team = get_object_or_404(Team, pk=teamID)
            event = team.event
        else:
            event = get_object_or_404(Event, pk=eventID)
        self.common(request, event, team, sourceTeam=sourceTeam)

        formInitial = {}
        studentsInitial = []
        if sourceTeam:
            formInitial = {
                'name': sourceTeam.name,
                'division': sourceTeam.division,
                'campus': sourceTeam.campus,
                'hardwarePlatform': sourceTeam.hardwarePlatform,
                'softwarePlatform': sourceTeam.softwarePlatform,
            }

            studentsInitial = []
            for student in sourceTeam.student_set.all():
                studentsInitial.append({
                    'firstName': student.firstName,
                    'lastName': student.lastName,
                    'yearLevel': student.yearLevel,
                    'gender': student.gender,
                })

        # Get form
        form = TeamForm(instance=team, user=request.user, event=event, initial=formInitial)
        formset = self.StudentInLineFormSet(instance=team, initial=studentsInitial)

        return render(request, 'teams/createEditTeam.html', {'form': form, 'formset':formset, 'event':event, 'team':team, 'divisionsMaxReachedWarnings': getDivisionsMaxReachedWarnings(event, request.user)})

    def post(self, request, eventID=None, teamID=None, sourceTeamID=None):
        sourceTeam = None
        event = None
        team = None
        if sourceTeamID is not None:
            sourceTeam = get_object_or_404(Team, pk=sourceTeamID)
            event = get_object_or_404(Event, pk=eventID)
        elif teamID is not None:
            team = get_object_or_404(Team, pk=teamID)
            event = team.event
        else:
            event = get_object_or_404(Event, pk=eventID)
        self.common(request, event, team, sourceTeam=sourceTeam)

        newTeam = team is None

        formset = self.StudentInLineFormSet(request.POST, instance=team, error_messages={"missing_management_form": "ManagementForm data is missing or has been tampered with"})
        form = TeamForm(request.POST, instance=team, user=request.user, event=event)

        if all([x.is_valid() for x in (form, formset)]):
            # Create team object but don't save so can set foreign keys
            team = form.save(commit=False)
            team.mentorUser = request.user

            if newTeam and sourceTeam:
                team.copiedFrom = sourceTeam

            # Save team
            team.save()

            # Save student formset
            if newTeam:
                # This is needed because it is possible to create teams and add students in one request
                formset.instance = team
            formset.save()

            # Redirect if add another in response
            if 'add_text' in request.POST and newTeam and not (event.maxEventTeamsForSchoolReached(request.user) or event.maxEventTeamsTotalReached()):
                return redirect(reverse('teams:create', kwargs = {"eventID":event.id}))

            elif not newTeam:
                return redirect(reverse('teams:details', kwargs = {"teamID":team.id}))

            return redirect(reverse('events:details', kwargs = {'eventID':event.id}))

        return render(request, 'teams/createEditTeam.html', {'form': form, 'formset':formset, 'event':event, 'team':team, 'divisionsMaxReachedWarnings': getDivisionsMaxReachedWarnings(event, request.user)})

def teamCreatePermissionForEvent(event):
    # Check event is published
    if not event.published():
        raise PermissionDenied("Event is not published")

    # Check registrations open
    if not event.registrationsOpen():
        raise PermissionDenied("Registration has closed for this event")

    if event.eventType != 'competition':
        raise PermissionDenied("Can only copy teams for competitions")

def checkEventLimitsReached(request, event):
    if event.maxEventTeamsForSchoolReached(request.user):
        raise PermissionDenied("Max teams for school for this event reached. Contact the organiser if you want to register more teams for this event.")

    if event.maxEventTeamsTotalReached():
        raise PermissionDenied("Max teams for this event reached. Contact the organiser if you want to register more teams for this event.")

@login_required
def copyTeamsList(request, eventID):
    event = get_object_or_404(Event, pk=eventID)

    teamCreatePermissionForEvent(event)

    try:
        checkEventLimitsReached(request, event)
    except PermissionDenied:
        return redirect(reverse('events:details', kwargs = {'eventID':event.id}))

    teams, copiedTeamsList, availableToCopyTeams = getAvailableToCopyTeams(request, event)
    availableToCopyTeams = availableToCopyTeams.prefetch_related('student_set', 'division', 'campus', 'event')

    copiedTeams = teams.filter(pk__in=copiedTeamsList)
    copiedTeams = copiedTeams.prefetch_related('student_set', 'division', 'campus', 'event')

    context = {
        'event': event,
        'availableToCopyTeams': availableToCopyTeams,
        'copiedTeams': copiedTeams,
        'showCampusColumn': teams.exclude(campus=None).exists(),
    }

    return render(request, 'teams/copyTeamsList.html', context)
