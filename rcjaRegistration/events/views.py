from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotAllowed
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError, PermissionDenied
from django.db.models import F, Q
from django.conf import settings
from coordination.permissions import checkCoordinatorPermission
from django.forms import formset_factory

import datetime, csv
import jwt

from .models import Event, BaseEventAttendance, Year, DivisionCategory
from regions.models import State
from teams.models import Team, Student
from schools.models import Campus
from workshops.models import WorkshopAttendee
from .forms import getSummaryForm, AdminEventsForm

# Need to check if schooladministrator is None

@login_required
def dashboard(request):
    # Events
    # Get user event filtering attributes
    if request.user.currentlySelectedSchool:
        usersEventAttendances = BaseEventAttendance.objects.filter(school=request.user.currentlySelectedSchool)
    else:
        usersEventAttendances = BaseEventAttendance.objects.filter(mentorUser=request.user, school=None)

    # Current state
    if request.user.currentlySelectedSchool:
        currentState = request.user.currentlySelectedSchool.state
    else:
        currentState = request.user.homeState

    # Get open events
    openForRegistrationEvents = Event.objects.filter(
        status='published',
        registrationsOpenDate__lte=datetime.datetime.today(),
        registrationsCloseDate__gte=datetime.datetime.today(),
    ).exclude(
        baseeventattendance__in=usersEventAttendances,
    ).prefetch_related('state', 'year').order_by('startDate').distinct()

    eventsAvailable = openForRegistrationEvents.exists()

    # Get not open events
    futureEvents = Event.objects.filter(
        Q(registrationsOpenDate__gt=datetime.datetime.today()) | Q(registrationsOpenDate__isnull=True),
        Q(startDate__gt=datetime.datetime.today()) | Q(startDate__isnull=True),
        status='published',
    ).exclude(
        pk__in=openForRegistrationEvents.values_list('pk', flat=True),
    ).exclude(
        baseeventattendance__in=usersEventAttendances,
    ).prefetch_related('state', 'year').order_by('startDate').distinct()

    # Filter open and future events by state
    if request.method == 'GET' and not 'viewAll' in request.GET:
        openForRegistrationEvents = openForRegistrationEvents.filter(Q(state=currentState) | Q(globalEvent=True) | Q(state__typeGlobal=True))
        futureEvents = futureEvents.filter(Q(state=currentState) | Q(globalEvent=True) | Q(state__typeGlobal=True))

    # Split competitions and workshops
    openForRegistrationCompetitions = openForRegistrationEvents.filter(eventType='competition')
    openForRegistrationWorkshops = openForRegistrationEvents.filter(eventType='workshop')

    # Get current and past events
    currentEvents = Event.objects.filter(
        endDate__gte=datetime.datetime.today(),
        baseeventattendance__in=usersEventAttendances,
        status="published",
    ).distinct().prefetch_related('state', 'year').order_by('startDate').distinct()

    pastEvents = Event.objects.filter(
        endDate__lt=datetime.datetime.today(),
        baseeventattendance__in=usersEventAttendances,
        status="published",
    ).prefetch_related('state', 'year').order_by('-startDate').distinct()

    # Invoices
    from invoices.models import Invoice
    invoices = Invoice.invoicesForUser(request.user)

    outstandingInvoices = sum([1 for invoice in invoices if invoice.amountDueInclGST() > 0.05]) # Rounded because consistent with what user sees and not used in subsequent calculations

    # Association join prompt
    showAssociationPrompt = not request.user.associationPromptShown
    if showAssociationPrompt:
        request.user.associationPromptShown = True
        request.user.save(update_fields=['associationPromptShown'], skipPrePostSave=True)

    context = {
        'futureEvents': futureEvents,
        'openForRegistrationCompetitions': openForRegistrationCompetitions,
        'openForRegistrationWorkshops': openForRegistrationWorkshops,
        'currentEvents': currentEvents,
        'pastEvents': pastEvents,
        'outstandingInvoices': outstandingInvoices,
        'invoices': invoices,
        'currentState': currentState,
        'eventsAvailable': eventsAvailable,
        'showAssociationPrompt': showAssociationPrompt
    }
    return render(request, 'events/dashboard.html', context)

def coordinatorEventDetailsPermissions(request, event):
    return checkCoordinatorPermission(request, Event, event, 'view')

def eventDetailsPermissions(request, event, filterDict):
    if coordinatorEventDetailsPermissions(request, event):
        return True

    if not event.published():
        return False

    if event.registrationsOpen():
        return True

    if event.registrationNotOpenYet():
        return True

    if BaseEventAttendance.objects.filter(**filterDict).exists():
        return True

    return False

def getDivisionsMaxReachedWarnings(event, user):
    # Get list of divisions that reached max number of teams
    divisionsMaxReachedWarnings = []
    for availableDivision in event.availabledivision_set.prefetch_related('division').all():
        if availableDivision.maxDivisionRegistrationsForSchoolReached(user):
            divisionsMaxReachedWarnings.append(f"{availableDivision.division}: Max {event.registrationName()}s for school for this event division reached. Contact the organiser if you want to register more {event.registrationName()}s in this division.")

        if availableDivision.maxDivisionRegistrationsTotalReached():
            divisionsMaxReachedWarnings.append(f"{availableDivision.division}: Max {event.registrationName()}s for this event division reached. Contact the organiser if you want to register more {event.registrationName()}s in this division.")

    return divisionsMaxReachedWarnings

def getAvailableToCopyTeams(request, event):
    # Get team filter dict
    filterDict = event.getBaseEventAttendanceFilterDict(request.user)

    # Get teams already copied
    copiedTeamsList = Team.objects.filter(**filterDict).filter(copiedFrom__isnull=False).values_list('copiedFrom', flat=True)

    # Replace event filtering with year filtering for current and previous event year
    del filterDict['event']
    filterDict['event__year__year__gte'] = event.year.year - 1
    filterDict['event__year__year__lte'] = event.year.year
    filterDict['event__status'] = 'published'

    availableDivisions = event.availabledivision_set.values_list('division', flat=True)

    # Get teams available to copy
    teams = Team.objects.filter(**filterDict)
    teams = teams.exclude(event=event) # Exclude teams of the current event
    availableToCopyTeams = teams.exclude(pk__in=copiedTeamsList) # Exclude already copied teams

    return teams, copiedTeamsList, availableToCopyTeams

@login_required
def details(request, eventID):
    event = get_object_or_404(Event, pk=eventID)

    # Get team and workshop attendee filter dict
    filterDict = event.getBaseEventAttendanceFilterDict(request.user)

    if not eventDetailsPermissions(request, event, filterDict):
        raise PermissionDenied("This event is unavailable")

    # Filter team or workshop attendee
    if event.boolWorkshop():
        teams = Team.objects.none()
        workshopAttendees = WorkshopAttendee.objects.filter(**filterDict)
    else:
        teams = Team.objects.filter(**filterDict)
        teams = teams.prefetch_related('student_set', 'division', 'campus', 'event')
        workshopAttendees = WorkshopAttendee.objects.none()

    # Get billing type label
    if event.boolWorkshop():
        billingTypeLabel = 'attendee'
    else:
        billingTypeLabel = event.competition_billingType

    _, _, availableToCopyTeams = getAvailableToCopyTeams(request, event)

    # Total registrations count for admins, excluding withdrawn teams
    if event.boolWorkshop():
        totalRegistrations = event.baseeventattendance_set.count()
    else:
        totalRegistrations = event.baseeventattendance_set.exclude(team__withdrawn=True).count()

    context = {
        'event': event,
        'availableDivisions': event.availabledivision_set.prefetch_related('division'),
        'divisionPricing': event.availabledivision_set.exclude(division_billingType='event').exists(),
        'teams': teams,
        'workshopAttendees': workshopAttendees,
        'showCampusColumn': BaseEventAttendance.objects.filter(**filterDict).exclude(campus=None).exists(),
        'billingTypeLabel': billingTypeLabel,
        'hasAdminPermissions': coordinatorEventDetailsPermissions(request, event),
        'maxEventRegistrationsForSchoolReached': event.maxEventRegistrationsForSchoolReached(request.user),
        'maxEventRegistrationsTotalReached': event.maxEventRegistrationsTotalReached(),
        'divisionsMaxReachedWarnings': getDivisionsMaxReachedWarnings(event, request.user),
        'duplicateTeamsAvailable': availableToCopyTeams.exists(),
        'totalRegistrations': totalRegistrations,
    }
    return render(request, 'events/details.html', context)

def cms(request, eventID):
    event = get_object_or_404(Event, pk=eventID)

    if event.cmsEventId:
        return redirect(settings.CMS_EVENT_URL_VIEW.replace("{EVENT_ID}", event.cmsEventId))

    # Check permissions for cms event creation
    # Only challenge coordinators with permission to change the event can create the CMS event instance for competitions
    if event.eventType != 'competition':
        raise PermissionDenied("The CMS for this event is unavailable")

    if not checkCoordinatorPermission(request, Event, event, 'change'):
        raise PermissionDenied("The CMS for this event is unavailable")

    cmsPayload = {
        "event": event.id,
        "user": request.user.id,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=settings.CMS_JWT_EXPIRY_MINUTES)
    }
    cmsToken = jwt.encode(cmsPayload, settings.CMS_JWT_SECRET, algorithm='HS256')
    return redirect(settings.CMS_EVENT_URL_CREATE.replace("{TOKEN}", cmsToken))

@login_required
def loggedInUnderConstruction(request):
    return render(request,'common/loggedInUnderConstruction.html')

def mentorEventAttendanceAccessPermissions(request, eventAttendance):
    if request.user.currentlySelectedSchool:
        # If user is a school administrator can only edit the currently selected school
        if request.user.currentlySelectedSchool != eventAttendance.school:
            return False

    else:
        # If not a school administrator allow editing individually entered eventAttendances
        if eventAttendance.mentorUser != request.user or eventAttendance.school:
            return False

    return True

class CreateEditBaseEventAttendance(LoginRequiredMixin, View):
    def common(self, request, event, eventAttendance):
        # Check is correct event type
        if event.eventType != self.eventType:
            raise PermissionDenied('Teams/ attendees cannot be created for this event type')

        # Check registrations open
        if not event.registrationsOpen():
            raise PermissionDenied("Registration has closed for this event")

        # Check event is published
        if not event.published():
            raise PermissionDenied("Event is not published")

        # Check administrator of this eventAttendance
        if eventAttendance and not mentorEventAttendanceAccessPermissions(request, eventAttendance):
            raise PermissionDenied("You are not an administrator of this team/ attendee")

        if not eventAttendance:
            if event.maxEventRegistrationsForSchoolReached(request.user):
                raise PermissionDenied(f"Max {event.registrationName()}s for school for this event reached. Contact the organiser if you want to register more {event.registrationName()}s for this event.")

            if event.maxEventRegistrationsTotalReached():
                raise PermissionDenied(f"Max {event.registrationName()}s for this event reached. Contact the organiser if you want to register more {event.registrationName()}s for this event.")

    def delete(self, request, teamID=None, attendeeID=None, eventID=None, sourceTeamID=None):
        # This endpoint should never be called with eventID or sourceTeamID
        if eventID or sourceTeamID:
            return HttpResponseForbidden()
        
        # Accept multiple variables because used for both teams and workshops
        # Need to lookup the relevant one
        eventAttendanceID = None
        if teamID is not None:
            eventAttendanceID = teamID
        if attendeeID is not None:
            eventAttendanceID = attendeeID

        eventAttendance = get_object_or_404(BaseEventAttendance, pk=eventAttendanceID)
        event = eventAttendance.event
        self.common(request, event, eventAttendance)

        # Delete team
        eventAttendance.delete()
        return HttpResponse(status=204)

def getEventsForSummary(state, year):
    """ Create list of event dictionaries of all events in state and year """
    eventList = Event.objects.filter(state = state, year = year).order_by('startDate', 'endDate')

    # Find information for events
    events = []
    for event in eventList:
        eventDict = {}
        eventDict["name"] = event.name

        if event.startDate==event.endDate:
            if event.startDate is not None:
                eventDict["date"] = event.startDate.strftime('%d/%m/%Y')
            else:
                eventDict["date"] = None
        else:
            eventDict["date"] = f"{event.startDate.strftime('%d/%m/%Y')} - {event.endDate.strftime('%d/%m/%Y')}"

        if event.eventType == "competition":
            # Initialise counting variables
            teamNumber = 0
            studentNumber = 0
            maleNumber = 0
            femaleNumber = 0
            otherNumber = 0

            # Count all teams
            attendances = BaseEventAttendance.objects.filter(event=event)
            for attendance in attendances:
                teamNumber += 1
                students = Student.objects.filter(team=attendance.childObject())
                for student in students:
                    studentNumber += 1
                    if student.gender == "male":
                        maleNumber += 1
                    elif student.gender == "female":
                        femaleNumber += 1
                    else:
                        otherNumber += 1

            # Create output
            if studentNumber > 0:
                mPercent = round(maleNumber/studentNumber*100)
                fPercent = round(femaleNumber/studentNumber*100)
                oPercent = round(otherNumber/studentNumber*100)
            else:
                mPercent, fPercent, oPercent = [0,0,0]
            eventDict["participants_one"] = f"Teams: {teamNumber}"
            eventDict["participants_two"] = f"Students: {studentNumber}"
            eventDict["participants_three"] = f"{fPercent}%F, {mPercent}%M, {oPercent}% other"
        else: # Workshop
            # Initialise counting variables
            studentNumber = 0
            teacherNumber = 0
            maleNumber = 0
            femaleNumber = 0
            otherNumber = 0

            # Count all students
            attendances = BaseEventAttendance.objects.filter(event=event)
            for attendance in attendances:
                attendance = attendance.childObject()
                if attendance.attendeeType == "student":
                    studentNumber += 1
                else:
                    teacherNumber += 1
                if attendance.gender == "male":
                    maleNumber += 1
                elif attendance.gender == "female":
                    femaleNumber += 1
                else:
                    otherNumber += 1

            # Create output
            if studentNumber + teacherNumber > 0:
                mPercent = round(maleNumber/(studentNumber+teacherNumber)*100)
                fPercent = round(femaleNumber/(studentNumber+teacherNumber)*100)
                oPercent = round(otherNumber/(studentNumber+teacherNumber)*100)
            else:
                mPercent, fPercent, oPercent = [0,0,0]
            eventDict["participants_one"] = f"Students: {studentNumber}"
            eventDict["participants_two"] = f"Teachers: {teacherNumber}"
            eventDict["participants_three"] = f"{fPercent}%F, {mPercent}%M, {oPercent}% other"

        if event.venue != None:
            eventDict["location"] = event.venue.name
        else:
            eventDict["location"] = "None"

        events.append(eventDict)

    return events

@login_required
def summaryReport(request):
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to view this page")

    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    form = getSummaryForm(request)
    if form.is_valid():
        selected_state = State.objects.get(id = form.cleaned_data["state"])
        selected_year = Year.objects.get(year = form.cleaned_data["year"])
        events = getEventsForSummary(selected_state, selected_year)
    else:
        events = []
        selected_state = None
        selected_year = None

    context = {
        "events": events,
        "form": form,
        'state': selected_state,
        'year': selected_year,
    }
    return render(request, 'events/summaryReport.html', context)

@login_required
def singlePageAdminSummary(request, eventID):
    event = get_object_or_404(Event, pk=eventID)
    if event.boolWorkshop():
        context = getAdminWorkSummary(event)
        return render(request, 'events/adminWorkshopDetails.html', context)
    else:
        context = getAdminCompSummary(event)
        return render(request, 'events/adminCompetitionDetails.html', context)

@login_required
def eventAdminSummary(request):
    output = ""
    if request.method == "POST":
        form = AdminEventsForm(request.POST)
        if form.is_valid():
            output = form.cleaned_data
            workshops = len(form.cleaned_data['workshops'])>0

            if workshops:
                events_list = form.cleaned_data['workshops']
                if len(events_list)==1:
                    event = get_object_or_404(Event, pk=events_list[0])
                    context = getAdminWorkSummary(event)
                    return render(request, 'events/adminWorkshopDetails.html', context)
                else:
                    events = [getAdminWorkSummary(get_object_or_404(Event, pk=event_id)) for event_id in events_list]
                    context =  mergeMultipleWorkshopsAdminSummary(events)
                    return render(request, 'events/adminMultiWorkDetails.html', context)
            else:
                events_list = form.cleaned_data['competitions']
                if len(events_list)==1:
                    event = get_object_or_404(Event, pk=events_list[0])
                    context = getAdminCompSummary(event)
                    return render(request, 'events/adminCompetitionDetails.html', context)
                else:
                    events = [getAdminCompSummary(get_object_or_404(Event, pk=event_id)) for event_id in events_list]
                    context = mergeMultipleCompsAdminSummary(events)
                    return render(request, 'events/adminMultiCompDetails.html', context)
    else:
        form = AdminEventsForm()
    return render(request, "events/adminBlank.html", {"form": form, 'output':output})

def mergeMultipleCompsAdminSummary(events):
    comps_number = len(events)

    # Divisions
    divisions = {'teams':[0]*comps_number,'students':[0]*comps_number,'categories':{}}
    for event_no, event in enumerate(events):
        for division_cat in event['division_categories'].values():
            division_cat_dict = divisions['categories'].get(division_cat['name'], {'name':division_cat['name'], 'divisions':{},'teams':[0]*comps_number,'students':[0]*comps_number})
            for division in division_cat['divisions']:
                division_dict = division_cat_dict['divisions'].get(division['name'], {'name':division['name'],'results':['Division not included']*comps_number})
                division_dict['results'][event_no] = {'teams':division['teams'],'students':division['students']}
                division_cat_dict['teams'][event_no] += division['teams']
                division_cat_dict['students'][event_no] += division['students']
                division_cat_dict['divisions'][division['name']] = division_dict
            divisions['categories'][division_cat['name']] = division_cat_dict
            divisions['students'][event_no] += division_cat_dict['students'][event_no]
            divisions['teams'][event_no] += division_cat_dict['teams'][event_no]


    for division_cat in divisions['categories']:
        rows = len(divisions['categories'][division_cat]['divisions'].keys())
        divisions['categories'][division_cat]['rows']=rows+1
    
    # Schools
    schools = {'teams':[0]*comps_number,'students':[0]*comps_number,'schools':{}}
    for event_no, event in enumerate(events):
        for school in event['schools']:
            school_dict = schools['schools'].get(school['name'], {'name':school['name'],'teams':[0]*comps_number,'students':[0]*comps_number})
            school_dict['teams'][event_no] += school['teams']
            school_dict['students'][event_no] += school['students']
            schools['schools'][school['name']] = school_dict
            schools['students'][event_no] += school_dict['students'][event_no]
            schools['teams'][event_no] += school_dict['teams'][event_no]

    context = {'divisions':divisions,
               'schools':schools,
               'events':events,}
    return context

def mergeMultipleWorkshopsAdminSummary(events):
    workshop_number = len(events)

    # Divisions
    divisions = {'students':[0]*workshop_number,'teachers':[0]*workshop_number,'categories':{}}
    for event_no, event in enumerate(events):
        for division_cat in event['division_categories'].values():
            division_cat_dict = divisions['categories'].get(division_cat['name'], {'name':division_cat['name'], 'divisions':{},'teachers':[0]*workshop_number,'students':[0]*workshop_number})
            for division in division_cat['divisions']:
                division_dict = division_cat_dict['divisions'].get(division['name'], {'name':division['name'],'results':['Division not included']*workshop_number})
                division_dict['results'][event_no] = {'teachers':division['teachers'],'students':division['students']}
                division_cat_dict['teachers'][event_no] += division['teachers']
                division_cat_dict['students'][event_no] += division['students']
                division_cat_dict['divisions'][division['name']] = division_dict
            divisions['categories'][division_cat['name']] = division_cat_dict
            divisions['students'][event_no] += division_cat_dict['students'][event_no]
            divisions['teachers'][event_no] += division_cat_dict['teachers'][event_no]


    for division_cat in divisions['categories']:
        rows = len(divisions['categories'][division_cat]['divisions'].keys())
        divisions['categories'][division_cat]['rows']=rows+1
    
    # Schools
    schools = {'teachers':[0]*workshop_number,'students':[0]*workshop_number,'schools':{}}
    for event_no, event in enumerate(events):
        for school in event['schools']:
            school_dict = schools['schools'].get(school['name'], {'name':school['name'],'teachers':[0]*workshop_number,'students':[0]*workshop_number})
            school_dict['teachers'][event_no] += school['teachers']
            school_dict['students'][event_no] += school['students']
            schools['schools'][school['name']] = school_dict
            schools['students'][event_no] += school_dict['students'][event_no]
            schools['teachers'][event_no] += school_dict['teachers'][event_no]

    context = {'divisions':divisions,
               'schools':schools,
               'events':events,}
    return context

def getAdminCompSummary(event):
    # Divisions
    divisionList = event.divisions.values()
    division_categories = {}
    division_teams = 0
    division_students = 0
    for division in divisionList.all():
        teams = Team.objects.filter(event = event).filter(division = division["id"])
        students = 0
        for team in teams:
            students += Student.objects.filter(team=team).count()  
        division_students += students
        division_teams += teams.count()
        divisionDict = {
            'name': division["name"],
            'teams': teams.count(),
            'students': students,
        }

        if division['category_id'] in division_categories:
           division_categories[division['category_id']]['divisions'].append(divisionDict)
           division_categories[division['category_id']]['rows'] += 1
           division_categories[division['category_id']]['students'] += students
           division_categories[division['category_id']]['teams'] += teams.count()
        else:
            division_categories[division['category_id']]={'name':DivisionCategory.objects.get(id=division['category_id']).name,
                                                          'divisions':[divisionDict], 
                                                          'rows': 2,
                                                          'students': students,
                                                          'teams': teams.count()}

    # Schools
    teams = Team.objects.filter(event = event)
    schools = {}
    school_teams = 0
    school_students = 0
    for team in teams:
        school = team.school
        students = Student.objects.filter(team=team).count()
        school_teams += 1
        school_students += students
        if school in schools:
            schools[school]['teams'] += 1
            schools[school]['students'] += students
        else:
            name = school.name if school is not None else 'Independent'
            schools[school] = {'name': name, 'teams': 1, 'students': students}
    
    independent = schools.pop(None, {'name': 'Independent', 'teams': 0, 'students': 0})
    school_list = list(schools.values())
    school_list.sort(key=lambda x: x['name'])
    school_list.append(independent)
    
    context = {
        "name": event.name,
        "year": str(event.year),
        "division_categories": division_categories,
        'division_teams': division_teams,
        'division_students': division_students,
        "schools": school_list,
        'school_teams': school_teams,
        'school_students': school_students,
    }
    return context

def getAdminWorkSummary(event):
    # Divisions
    divisionList = event.divisions.values()
    division_categories = {}
    division_teachers = 0
    division_students = 0
    for division in divisionList.all():
        students = WorkshopAttendee.objects.filter(event=event, division=division['id'], attendeeType='student').count()
        teachers = WorkshopAttendee.objects.filter(event=event, division=division['id'], attendeeType='teacher').count()
        division_students += students
        division_teachers += teachers
        divisionDict = {
            'name': division["name"],
            'students': students,
            'teachers': teachers,
        }

        if division['category_id'] in division_categories:
           division_categories[division['category_id']]['divisions'].append(divisionDict)
           division_categories[division['category_id']]['rows'] += 1
           division_categories[division['category_id']]['teachers'] += teachers
           division_categories[division['category_id']]['students'] += students
        else:
            division_categories[division['category_id']]={'name':DivisionCategory.objects.get(id=division['category_id']).name,
                                                          'divisions':[divisionDict], 
                                                          'rows': 2,
                                                          'teachers': teachers,
                                                          'students': students}

    # Change rows to strings
    for division_cat in division_categories.values():
        division_cat["rows"] = division_cat["rows"]

    # Schools
    schools = {}
    school_teachers = 0
    school_students = 0
    attendees = WorkshopAttendee.objects.filter(event=event)
    for attendee in attendees:
        school = attendee.school
        students = 0
        teachers = 0
        if attendee.attendeeType=='student':
            school_students+= 1
            students += 1
        else:
            school_teachers += 1
            teachers += 1

        if school in schools:
            schools[school]['students'] += students
            schools[school]['teachers'] += teachers
        else:
            name = school.name if school is not None else 'Independent'
            schools[school] = {'name': name, 'students': students, 'teachers': teachers}
    
    independent = schools.pop(None, {'name': 'Independent', 'students': 0, 'teachers': 0})
    school_list = list(schools.values())
    school_list.sort(key=lambda x: x['name'])
    school_list.append(independent)
    
    context = {
        "name": event.name,
        "year": str(event.year),
        "division_categories": division_categories,
        'division_teachers': division_teachers,
        'division_students': division_students,
        "schools": school_list,
        'school_teachers': school_teachers,
        'school_students': school_students,
    }
    return context

@login_required
def comp_summary_csv(request):
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to view this page")
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Competition Attendance Summary.csv"'
    t = loader.get_template("events/adminCompCsv.txt")
    events = [event for event in Event.objects.filter(eventType='competition') 
              if BaseEventAttendance.objects.filter(event=event).count()
              and checkCoordinatorPermission(request, Event, event, 'view')]
    events = [getAdminCompSummary(event) for event in events]
    context =  mergeMultipleCompsAdminSummary(events)
    response.write(t.render(context))
    return response

@login_required
def workshop_summary_csv(request):
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to view this page")
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Workshop Attendance Summary.csv"'

    t = loader.get_template("events/adminWorkshopCsv.txt")
    events = [event for event in Event.objects.filter(eventType='workshop') 
              if BaseEventAttendance.objects.filter(event=event).count() 
              and checkCoordinatorPermission(request, Event, event, 'view')]
    events = [getAdminWorkSummary(event) for event in events]
    context =  mergeMultipleWorkshopsAdminSummary(events)
    response.write(t.render(context))
    return response