from django.shortcuts import render, get_object_or_404,redirect
from .models import Student,Team
from django.core.exceptions import ValidationError,PermissionDenied
from .forms import TeamForm,StudentForm
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory, inlineformset_factory
from events.models import Event
from django.http import HttpResponse
from django.urls import reverse
import datetime
# Create your views here.
@login_required
def createTeam(request,eventID): #TODO!! validate eventID is one that teams can be created for
    event = get_object_or_404(Event, pk=eventID)
    StudentInLineFormSet = inlineformset_factory(Team,Student,form=StudentForm,extra=event.max_team_members,max_num=event.max_team_members,can_delete=False)
    if event.registrationsCloseDate < datetime.datetime.now().date():
        raise PermissionDenied("Registrtaion has closed for this event!")
    if request.method == 'POST':
        formset = StudentInLineFormSet(request.POST)
        form = TeamForm(request.POST)
        form.event_id = eventID #NOTE: this is a custom property assignment, see forms.py
        if form.is_valid() and formset.is_valid():
            team = form.save(commit=False)
            team.event_id = eventID
            team.school = request.user.mentor.school
            team = form.save()
            formset.instance = team
            formset.save() 
            if 'add_text' in request.POST:
                return redirect(reverse('teams:create', eventID = event.id))
            return redirect('/')
    else:
        form = TeamForm()
        formset = StudentInLineFormSet()
    return render(request, 'teams/addTeam.html', {'form': form, 'formset':formset,'event':event})
@login_required
def editTeam(request,teamID):
    team = get_object_or_404(Team, pk=teamID)
    event = team.event
    if event.registrationsCloseDate < datetime.datetime.now().date():
        raise PermissionDenied("Registrtaion has closed for this event!")
    if request.user.mentor.school != team.school:
        raise PermissionDenied("You are not a mentor of this Team!")
    StudentInLineFormSet = inlineformset_factory(Team,Student,form=StudentForm,extra=event.max_team_members,max_num=event.max_team_members,can_delete=True)

    if request.method == 'POST':
        formset = StudentInLineFormSet(request.POST,instance=team)
        form = TeamForm(request.POST,instance=team)
        form.event_id = event.id
        form.team_id = team.id
        if form.is_valid() and formset.is_valid():
            team = form.save(commit=False)
            team = form.save()
            formset.save() 

            return redirect(reverse('events:summary', eventID = event.id))
    else:
        form = TeamForm(instance=team)
        formset = StudentInLineFormSet(instance=team)
    return render(request, 'teams/addTeam.html', {'form': form, 'formset':formset,'event':event,'team':team})
@login_required
def deleteTeam(request): 
    #validate mentor is mentor of the team
    if request.method == 'POST':
        team = get_object_or_404(Team,pk=request.POST["teamID"])
        if team.event.registrationsCloseDate < datetime.datetime.now().date():
            raise PermissionDenied("Registrtaion has closed for this event!")
        if request.user.mentor.school == team.school:
            team.delete()
            return HttpResponse(status=200)
        else:
            raise PermissionDenied("You are not a mentor of this Team!")
