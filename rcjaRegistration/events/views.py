from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError, PermissionDenied
from django.db.models import F, Q
from coordination.permissions import checkCoordinatorPermission

import datetime

from .models import Event, BaseEventAttendance, DivisionCategory
from teams.models import Team, Student
from schools.models import Campus
from workshops.models import WorkshopAttendee

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

    # Filter open events by state
    if request.method == 'GET' and not 'viewAll' in request.GET:
        openForRegistrationEvents = openForRegistrationEvents.filter(Q(state=currentState) | Q(globalEvent=True) | Q(state__typeGlobal=True))

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

    context = {
        'openForRegistrationCompetitions': openForRegistrationCompetitions,
        'openForRegistrationWorkshops': openForRegistrationWorkshops,
        'currentEvents': currentEvents,
        'pastEvents': pastEvents,
        'outstandingInvoices': outstandingInvoices,
        'invoices': invoices,
        'currentState': currentState,
        'eventsAvailable': eventsAvailable,
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
        if availableDivision.maxDivisionTeamsForSchoolReached(user):
            divisionsMaxReachedWarnings.append(f"{availableDivision.division}: Max teams for school for this event division reached. Contact the organiser if you want to register more teams in this division.")

        if availableDivision.maxDivisionTeamsTotalReached():
            divisionsMaxReachedWarnings.append(f"{availableDivision.division}: Max teams for this event division reached. Contact the organiser if you want to register more teams in this division.")
    
    return divisionsMaxReachedWarnings

def getAvailableToCopyTeams(request, event):
    # Get team filter dict
    filterDict = event.getBaseEventAttendanceFilterDict(request.user)

    # Get teams already copied
    copiedTeamsList = Team.objects.filter(**filterDict).filter(copiedFrom__isnull=False).values_list('copiedFrom', flat=True)

    # Replace event filtering with year filtering
    del filterDict['event']
    filterDict['event__year'] = event.year
    filterDict['event__status'] = 'published'

    availableDivisions = event.availabledivision_set.values_list('division', flat=True)

    # Get teams available to copy
    teams = Team.objects.filter(**filterDict)
    teams = teams.exclude(event=event) # Exclude teams of the current event
    availableToCopyTeams = teams.exclude(pk__in=copiedTeamsList) # Exclude already copied teams
    availableToCopyTeams = availableToCopyTeams.filter(division__in=availableDivisions) # Filter to teams that have a division compatible with the target event

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
        billingTypeLabel = event.event_billingType

    _, _, availableToCopyTeams = getAvailableToCopyTeams(request, event)

    context = {
        'event': event,
        'availableDivisions': event.availabledivision_set.prefetch_related('division'),
        'divisionPricing': event.availabledivision_set.exclude(division_billingType='event').exists(),
        'teams': teams,
        'workshopAttendees': workshopAttendees,
        'showCampusColumn': BaseEventAttendance.objects.filter(**filterDict).exclude(campus=None).exists(),
        'billingTypeLabel': billingTypeLabel,
        'hasAdminPermissions': coordinatorEventDetailsPermissions(request, event),
        'maxEventTeamsForSchoolReached': event.maxEventTeamsForSchoolReached(request.user),
        'maxEventTeamsTotalReached': event.maxEventTeamsTotalReached(),
        'divisionsMaxReachedWarnings': getDivisionsMaxReachedWarnings(event, request.user),
        'duplicateTeamsAvailable': availableToCopyTeams.exists(),
    }
    return render(request, 'events/details.html', context)   

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

    def delete(self, request, teamID=None, attendeeID=None, eventID=None):
        # This endpoint should never be called with eventID
        if eventID is not None:
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

@login_required
def eventAdminSummary(request, events):
    events_list = events.split('/')
    if len(events_list)==1:
        event = get_object_or_404(Event, pk=events_list[0])
        return singlePageAdminSummary(request, event)
    else:
        events = [get_object_or_404(Event, pk=event_id) for event_id in events_list]
        multiplePageAdminSummary(request, events)
    
def singlePageAdminSummary(request, event):
    if event.boolWorkshop():
        context = getAdminWorkSummary(event)
        return render(request, 'events/adminWorkshopDetails.html', context)
    else:
        context = getAdminCompSummary(event)
        return render(request, 'events/adminCompetitionDetails.html', context)

def multiplePageAdminSummary(request, events):
    competition = False
    workshop = False
    context = {'events'}
    for event in events:
        if event.boolWorkshop():
            workshop = True
            context['events'].append(getAdminWorkSummary(event))
        else:
            competition = True
            context['events'].append(getAdminCompSummary(event))

    if competition and workshop:
        raise IndexError
    elif competition:
        return render(request, 'events/adminMultiCompDetails.html', context)
    elif workshop:
        return render(request, 'events/adminMultiWorkDetails.html', context)
    else:
        raise KeyError

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
                                                          'rows': 3,
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
    school_list.sort()
    school_list.append(independent)
    
    context = {
        "name": event.name,
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
                                                          'rows': 3,
                                                          'teachers': teachers,
                                                          'students': students}

    # Change rows to strings
    for division_cat in division_categories.values():
        division_cat["rows"] = str(division_cat["rows"])

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
    school_list.sort()
    school_list.append(independent)
    
    context = {
        "name": event.name,
        "division_categories": division_categories,
        'division_teachers': division_teachers,
        'division_students': division_students,
        "schools": school_list,
        'school_teachers': school_teachers,
        'school_students': school_students,
    }
    return context