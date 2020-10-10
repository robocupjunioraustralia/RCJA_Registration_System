from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError, PermissionDenied

import datetime

from .models import *
from teams.models import Team
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
    ).order_by('startDate').distinct()

    eventsAvailable = openForRegistrationEvents.exists()

    # Filter open events by state
    if request.method == 'GET' and not 'viewAll' in request.GET:
        openForRegistrationEvents = openForRegistrationEvents.filter(Q(state=currentState) | Q(globalEvent=True))

    # Split competitions and workshops
    openForRegistrationCompetitions = openForRegistrationEvents.filter(eventType='competition')
    openForRegistrationWorkshops = openForRegistrationEvents.filter(eventType='workshop')

    # Get current and past events
    currentEvents = Event.objects.filter(
        endDate__gte=datetime.datetime.today(),
        baseeventattendance__in=usersEventAttendances,
    ).distinct().order_by('startDate').distinct()

    pastEvents = Event.objects.filter(
        endDate__lt=datetime.datetime.today(),
        baseeventattendance__in=usersEventAttendances,
    ).order_by('-startDate').distinct()

    # Invoices
    from invoices.models import Invoice
    invoices = Invoice.invoicesForUser(request.user)

    outstandingInvoices = sum([1 for invoice in invoices if invoice.amountDueInclGST() > 0])

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
    from coordination.adminPermissions import checkStatePermissions
    return checkStatePermissions(request, event, 'view')

def mentorEventDetailsPermissions_currentEvent(request, event):
    return event.status == 'published' and event.registrationsOpen()

@login_required
def details(request, eventID):
    event = get_object_or_404(Event, pk=eventID)

    # Get team and workshop attendee filter dict
    if request.user.currentlySelectedSchool:
        filterDict = {
            'school': request.user.currentlySelectedSchool,
            'event': event,
        }
    else:
        filterDict = {
            'mentorUser': request.user,
            'school': None,
            'event': event,
        }

    if not (coordinatorEventDetailsPermissions(request, event) or mentorEventDetailsPermissions_currentEvent(request, event) or BaseEventAttendance.objects.filter(**filterDict).exists()):
        raise PermissionDenied("This event is unavailable")

    # Filter team or workshop attendee
    if event.boolWorkshop():
        teams = Team.objects.none()
        workshopAttendees = WorkshopAttendee.objects.filter(**filterDict)
    else:
        teams = Team.objects.filter(**filterDict)
        teams = teams.prefetch_related('student_set')
        workshopAttendees = WorkshopAttendee.objects.none()

    # Get billing type label
    if event.boolWorkshop():
        billingTypeLabel = 'attendee'
    else:
        billingTypeLabel = event.event_billingType

    context = {
        'event': event,
        'divisionPricing': event.availabledivision_set.exclude(division_billingType='event').exists(),
        'teams': teams,
        'workshopAttendees': workshopAttendees,
        'showCampusColumn': BaseEventAttendance.objects.filter(**filterDict).exclude(campus=None).exists(),
        'billingTypeLabel': billingTypeLabel,
    }
    return render(request, 'events/details.html', context)   

@login_required
def loggedInUnderConstruction(request):
    return render(request,'common/loggedInUnderConstruction.html') 

def eventAttendancePermissions(request, eventAttendance):
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
    def common(self, request, event, obj):
        # Check is correct event type
        if event.eventType != self.eventType:
            raise PermissionDenied('Teams/ attendees cannot be created for this event type')

        # Check registrations open
        if not event.registrationsOpen():
            raise PermissionDenied("Registration has closed for this event")

        if event.status != 'published':
            raise PermissionDenied("Event is not published")

        # Check administrator of this obj
        if obj and not eventAttendancePermissions(request, obj):
            raise PermissionDenied("You are not an administrator of this team/ attendee")

    def delete(self, request, objID):
        obj = get_object_or_404(BaseEventAttendance, pk=objID)
        event = obj.event
        self.common(request, event, obj)

        # Delete team
        obj.delete()
        return HttpResponse(status=204)
