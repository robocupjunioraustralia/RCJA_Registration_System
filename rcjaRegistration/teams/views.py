from django.shortcuts import render, get_object_or_404, redirect
from .models import Student,Team
from django.core.exceptions import ValidationError, PermissionDenied
from .forms import TeamForm,StudentForm
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory, inlineformset_factory
from events.models import Event
from django.http import HttpResponse, HttpResponseNotFound
from django.urls import reverse
import datetime

# Create your views here.

@login_required
def createTeam(request, eventID): #TODO!! validate eventID is one that teams can be created for
    event = get_object_or_404(Event, pk=eventID)

    StudentInLineFormSet = inlineformset_factory(Team, Student, form=StudentForm, extra=event.max_team_members, max_num=event.max_team_members, can_delete=False)

    if event.registrationsCloseDate < datetime.datetime.now().date():
        raise PermissionDenied("Registrtaion has closed for this event")

    if request.method == 'POST':
        formset = StudentInLineFormSet(request.POST)
        form = TeamForm(request.POST, event_id=eventID, user=request.user)
        form.event_id = eventID #NOTE: this is a custom property assignment, see forms.py
        if form.is_valid() and formset.is_valid():
            # Create team object but don't save so can set foreign keys
            team = form.save(commit=False)
            team.event = event
            team.mentorUser = request.user
            team.school = request.user.currentlySelectedSchool

            # Save team
            team.save()

            # Save student formset
            formset.instance = team
            formset.save() 
            if 'add_text' in request.POST:
                return redirect(reverse('teams:create', kwargs = {"eventID":event.id}))
            return redirect(reverse('events:summary', kwargs = {'eventID':event.id}))

    else:
        # Get default campus if only one campus for school
        if request.user.currentlySelectedSchool:
            campuses = request.user.currentlySelectedSchool.campus_set.all()
            defaultCampus = campuses.first() if campuses.count() == 1 else None
        else:
            defaultCampus = None

        # Create form
        form = TeamForm(event_id=eventID, user=request.user, initial={'campus':defaultCampus})
        formset = StudentInLineFormSet()
    return render(request, 'teams/addTeam.html', {'form': form, 'formset':formset,'event':event})

@login_required
def editTeam(request, teamID):
    team = get_object_or_404(Team, pk=teamID)
    event = team.event

    # Check registrations open
    # TODO: Add a view page or move this to the post
    if event.registrationsCloseDate < datetime.datetime.now().date():
        raise PermissionDenied("Registrtaion has closed for this event!")

    # Check administrator of this team
    if request.user.currentlySelectedSchool:
        # If user is a school administrator can only edit the currently selected school
        if request.user.currentlySelectedSchool != team.school:
            raise PermissionDenied("You are not an administrator of this team")

    else:
        # If not a school administrator allow editing individually entered teams
        if team.mentorUser != request.user or team.school:
            raise PermissionDenied("You are not an administrator of this team")

    StudentInLineFormSet = inlineformset_factory(Team,Student,form=StudentForm,extra=event.max_team_members,max_num=event.max_team_members,can_delete=True)

    if request.method == 'POST':
        formset = StudentInLineFormSet(request.POST,instance=team)
        form = TeamForm(request.POST,instance=team, event_id=event.id, user=request.user)
        form.event_id = event.id
        form.team_id = team.id
        if form.is_valid() and formset.is_valid():
            # Create team object but don't save so can set foreign keys
            team = form.save(commit=False)
            team.mentorUser = request.user

            # Save team
            team.save()

            # Save student formset
            formset.save() 

            return redirect(reverse('events:summary', kwargs = {"eventID":event.id}))
    else:
        form = TeamForm(instance=team, event_id=event.id, user=request.user)
        formset = StudentInLineFormSet(instance=team)
    return render(request, 'teams/addTeam.html', {'form': form, 'formset':formset,'event':event,'team':team})

@login_required
def deleteTeam(request, teamID): 
    # validate schooladministrator is schooladministrator of the team
    if request.method == 'DELETE':
        team = get_object_or_404(Team, pk=teamID)

        # Check registrations open
        if team.event.registrationsCloseDate < datetime.datetime.now().date():
            raise PermissionDenied("Registrtaion has closed for this event!")

            # Check administrator of this team
        if request.user.currentlySelectedSchool:
            # If user is a school administrator can only edit the currently selected school
            if request.user.currentlySelectedSchool != team.school:
                raise PermissionDenied("You are not an administrator of this team")

        else:
            # If not a school administrator allow editing individually entered teams
            if team.mentorUser != request.user or team.school:
                raise PermissionDenied("You are not an administrator of this team")

        # Delete team
        team.delete()
        return HttpResponse(status=200)
    return HttpResponseNotFound('Can only do delete methods on this page')
