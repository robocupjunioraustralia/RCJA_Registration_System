from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth.decorators import login_required

import datetime

from .models import *
from teams.models import Team

# Need to check if schooladministrator is None

@login_required
def index(request):
    # Events
    # Get user event filtering attributes
    if request.user.currentlySelectedSchool:
        usersTeams = Team.objects.filter(school=request.user.currentlySelectedSchool)
    else:
        usersTeams = request.user.team_set.filter(school=None)

    # Current state
    if request.user.currentlySelectedSchool:
        currentState = request.user.currentlySelectedSchool.state
    else:
        currentState = request.user.homeState

    openForRegistrationEvents = Event.objects.filter(
        registrationsOpenDate__lte=datetime.datetime.today(),
        registrationsCloseDate__gte=datetime.datetime.today(),
    ).exclude(
        team__in=usersTeams,
    ).order_by('startDate').distinct()

    # viewingAll = False
    if request.method == 'GET' and not 'viewAll' in request.GET:
        openForRegistrationEvents = openForRegistrationEvents.filter(Q(state=currentState) | Q(globalEvent=True))

    if not request.user.currentlySelectedSchool:
        openForRegistrationEvents = openForRegistrationEvents.exclude()

    currentEvents = Event.objects.filter(
        endDate__gte=datetime.datetime.today(),
        team__in=usersTeams,
    ).distinct().order_by('startDate').distinct()

    pastEvents = Event.objects.filter(
        endDate__lt=datetime.datetime.today(),
        team__in=usersTeams,
    ).order_by('-startDate').distinct()

    # Invoices
    from invoices.models import Invoice
    invoices = Invoice.objects.filter(Q(school__schooladministrator__user=request.user) | Q(invoiceToUser=request.user)).distinct()

    outstandingInvoices = sum([1 for invoice in invoices if invoice.amountDueInclGST() > 0])

    context = {
        'openForRegistrationEvents': openForRegistrationEvents,
        'currentEvents': currentEvents,
        'pastEvents': pastEvents,
        'outstandingInvoices': outstandingInvoices,
        'invoices': invoices
    }
    return render(request, 'events/eventList.html', context)

# Currently unused and not in urlconf
# Changes to permissions checks required before used
@login_required
def detail(request, eventID):
    event = get_object_or_404(Event, pk=eventID)
    teams = Team.objects.filter(school__schooladministrator__user=request.user, event__pk=eventID).prefetch_related('student_set')
    context = {
        'event': event,
        'teams': teams,
        'today':datetime.date.today()
    }
    return render(request, 'events/eventDetail.html', context)

@login_required
def summary(request, eventID):
    event = get_object_or_404(Event, pk=eventID)

    # filter teams
    if request.user.currentlySelectedSchool:
        teams = Team.objects.filter(school=request.user.currentlySelectedSchool, event=event)
    else:
        teams = request.user.team_set.filter(event=event, school=None)
    
    teams = teams.prefetch_related('student_set')

    context = {
        'event': event,
        'teams': teams,
        'today':datetime.date.today()
    }
    return render(request, 'events/eventSummary.html', context)   

@login_required
def loggedInUnderConstruction(request):
    return render(request,'common/loggedInUnderConstruction.html') 

