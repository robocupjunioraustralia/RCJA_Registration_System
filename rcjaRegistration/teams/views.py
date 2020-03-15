from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory, inlineformset_factory
from django.http import HttpResponse, HttpResponseForbidden
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import TeamForm, StudentForm

from .models import Student, Team
from events.models import Event

import datetime

# Create your views here.

def teamPermissions(request, team):
    if request.user.currentlySelectedSchool:
        # If user is a school administrator can only edit the currently selected school
        if request.user.currentlySelectedSchool != team.school:
            return False

    else:
        # If not a school administrator allow editing individually entered teams
        if team.mentorUser != request.user or team.school:
            return False
    
    return True

class CreateEditTeam(LoginRequiredMixin, View):
    def common(self, request, event, team=None):
        # Check is competition for team
        if not event.eventType == 'competition':
            raise PermissionDenied('Teams cannot be created for this event type')

        # Check registrations open
        if event.registrationsCloseDate < datetime.datetime.now().date():
            raise PermissionDenied("Registrtaion has closed for this event!")

        # Check administrator of this team
        if team and not teamPermissions(request, team):
            raise PermissionDenied("You are not an administrator of this team")

        self.StudentInLineFormSet = inlineformset_factory(
            Team,
            Student,
            form = StudentForm,
            extra = event.maxMembersPerTeam,
            max_num = event.maxMembersPerTeam,
            can_delete = team is not None,
        )

    def get(self, request, event, team=None):
        self.common(request, event, team)

        # Get form
        form = TeamForm(instance=team, user=request.user, event=event)
        formset = self.StudentInLineFormSet(instance=team)

        return render(request, 'teams/addEditTeam.html', {'form': form, 'formset':formset, 'event':event, 'team':team})

    def post(self, request, event, team=None):
        self.common(request, event, team)

        newTeam = team is None

        formset = self.StudentInLineFormSet(request.POST, instance=team)
        form = TeamForm(request.POST, instance=team, user=request.user, event=event)
        form.mentorUser = request.user # Needed in form validation to check number of teams for independents not exceeded

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

            return redirect(reverse('events:details', kwargs = {'eventID':event.id}))

        # Default to displaying the form again if form not valid
        return render(request, 'teams/addEditTeam.html', {'form': form, 'formset':formset, 'event':event})

class CreateTeam(CreateEditTeam):
    def get(self, request, eventID):
        event = get_object_or_404(Event, pk=eventID)
        return super().get(request, event)

    def post(self, request, eventID):
        event = get_object_or_404(Event, pk=eventID)
        return super().post(request, event)

class EditTeam(CreateEditTeam):
    def get(self, request, teamID):
        team = get_object_or_404(Team, pk=teamID)
        event = team.event
        return super().get(request, event, team)

    def post(self, request, teamID):
        team = get_object_or_404(Team, pk=teamID)
        event = team.event
        return super().post(request, event, team)

@login_required
def deleteTeam(request, teamID): 
    # validate schooladministrator is schooladministrator of the team
    if request.method == 'DELETE':
        team = get_object_or_404(Team, pk=teamID)

        # Check registrations open
        if team.event.registrationsCloseDate < datetime.datetime.now().date():
            raise PermissionDenied("Registrtaion has closed for this event!")

        # Check administrator of this team
        if not teamPermissions(request, team):
            raise PermissionDenied("You are not an administrator of this team")

        # Delete team
        team.delete()
        return HttpResponse(status=204)
    return HttpResponseForbidden()
