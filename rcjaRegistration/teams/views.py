from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.forms import modelformset_factory, inlineformset_factory
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.urls import reverse

from .forms import TeamForm, StudentForm, ImportTeamsCSVForm

import csv
import datetime

from .models import Student, Team
from events.models import Event, AvailableDivision

from events.views import CreateEditBaseEventAttendance, mentorEventAttendanceAccessPermissions, getDivisionsMaxReachedWarnings, getAvailableToCopyTeams, createPermissionForEvent, checkEventLimitsReached

from . import csvImport

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
                raise PermissionDenied("Team source event can not be same as destination event.")
            
            # Check source team event is published
            if not sourceTeam.event.published():
                raise PermissionDenied("Team source event is not published.")

            #  Check source team event year is current or previous year
            if sourceTeam.event.year.year < event.year.year - 1 or sourceTeam.event.year.year > event.year.year:
                raise PermissionDenied("Team source event year must be current or previous year.")

        self.StudentInLineFormSet = inlineformset_factory(
            Team,
            Student,
            form = StudentForm,
            min_num = 1,
            extra = sourceTeam.student_set.count() - 1 if sourceTeam else 0,
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
                    'yearLevel': student.yearLevel + event.year.year - sourceTeam.event.year.year,
                    'gender': student.gender,
                })

        # Get form
        form = TeamForm(instance=team, user=request.user, event=event, initial=formInitial)
        formset = self.StudentInLineFormSet(instance=team, initial=studentsInitial)

        return render(request, 'teams/createEditTeam.html', {'form': form, 'formset':formset, 'event':event, 'team':team, 'sourceTeam': sourceTeam, 'divisionsMaxReachedWarnings': getDivisionsMaxReachedWarnings(event, request.user)})

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
            if 'add_text' in request.POST and newTeam and not (event.maxEventRegistrationsForSchoolReached(request.user) or event.maxEventRegistrationsTotalReached()):
                return redirect(reverse('teams:create', kwargs = {"eventID":event.id}))

            if sourceTeam:
                return redirect(reverse('teams:copyTeamsList', kwargs = {'eventID':event.id}))

            elif not newTeam:
                return redirect(reverse('teams:details', kwargs = {"teamID":team.id}))

            return redirect(reverse('events:details', kwargs = {'eventID':event.id}))

        return render(request, 'teams/createEditTeam.html', {'form': form, 'formset':formset, 'event':event, 'team':team, 'sourceTeam': sourceTeam, 'divisionsMaxReachedWarnings': getDivisionsMaxReachedWarnings(event, request.user)})

@login_required
def copyTeamsList(request, eventID):
    event = get_object_or_404(Event, pk=eventID)

    createPermissionForEvent(event, 'competition')

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

@login_required
def importTeamsCSVTemplate(request, eventID):
    event = get_object_or_404(Event, pk=eventID)

    # Same checks as the import page, so the template can't be downloaded for an event that can't be registered for
    createPermissionForEvent(event, 'competition')
    checkEventLimitsReached(request, event)

    response = HttpResponse(content_type='text/csv')
    # Quoted because the event name includes the state in brackets
    response['Content-Disposition'] = f'attachment; filename="{event} Team Import Template.csv"'

    writer = csv.writer(response)
    writer.writerow(csvImport.csvHeaders(event, request.user))

    return response

class ImportTeamsCSV(CreateEditBaseEventAttendance):
    eventType = 'competition'

    def context(self, request, event, **kwargs):
        optionHeaders, optionRows = csvImport.optionsTable(event, request.user)

        context = {
            'event': event,
            'form': ImportTeamsCSVForm(),
            'optionHeaders': optionHeaders,
            'optionRows': optionRows,
            'showCampusColumn': csvImport.campusFieldRelevant(request.user),
            'divisionsMaxReachedWarnings': getDivisionsMaxReachedWarnings(event, request.user),
        }
        context.update(kwargs)

        return context

    def get(self, request, eventID):
        event = get_object_or_404(Event, pk=eventID)
        self.common(request, event, None)

        return render(request, 'teams/importTeamsCSV.html', self.context(request, event))

    def post(self, request, eventID):
        event = get_object_or_404(Event, pk=eventID)
        self.common(request, event, None)

        if 'import' in request.POST:
            return self.importTeams(request, event)

        return self.preview(request, event)

    def preview(self, request, event):
        # Validates and displays the teams in the uploaded file, does not create anything
        form = ImportTeamsCSVForm(request.POST, request.FILES)

        if not form.is_valid():
            return render(request, 'teams/importTeamsCSV.html', self.context(request, event, form=form))

        csvText, fileError = csvImport.readUploadedFile(form.cleaned_data['csvFile'])

        if fileError:
            return render(request, 'teams/importTeamsCSV.html', self.context(request, event, fileErrors=[fileError]))

        importedTeams, fileErrors = csvImport.parseAndValidateCSV(event, request.user, csvText)

        return render(request, 'teams/importTeamsCSV.html', self.context(
            request,
            event,
            importedTeams = importedTeams,
            fileErrors = fileErrors,
            csvText = csvText,
            showImportButton = bool(importedTeams) and not fileErrors and not csvImport.hasErrors(importedTeams),
        ))

    def importTeams(self, request, event):
        # The csv is re-posted from the preview page so it must be validated again before anything is created
        csvText = request.POST.get('csvText', '')

        importedTeams, fileErrors = csvImport.parseAndValidateCSV(event, request.user, csvText)

        if fileErrors or not importedTeams or csvImport.hasErrors(importedTeams):
            return render(request, 'teams/importTeamsCSV.html', self.context(
                request,
                event,
                importedTeams = importedTeams,
                fileErrors = fileErrors,
                csvText = csvText,
                showImportButton = False,
            ))

        # All or nothing, so a failure part way through does not leave a partially imported event
        with transaction.atomic():
            for importedTeam in importedTeams:
                team = importedTeam.teamForm.save(commit=False)
                team.csv_imported = True
                team.save()

                for studentForm in importedTeam.studentForms:
                    student = studentForm.save(commit=False)
                    student.team = team
                    student.save()

        return redirect(reverse('events:details', kwargs={'eventID': event.id}))
