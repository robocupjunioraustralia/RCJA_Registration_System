from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

import datetime

from .models import *

# Need to check if mentor is None

@login_required
def index(request):
    # Events
    openForRegistrationEvents = Event.objects.filter(registrationsOpenDate__lte=datetime.datetime.today(), registrationsCloseDate__gte=datetime.datetime.today()).exclude(team__school__mentor__user=request.user).order_by('startDate').distinct()
    currentEvents = Event.objects.filter(endDate__gte=datetime.datetime.today(), team__school__mentor__user=request.user).distinct().order_by('startDate').distinct()
    pastEvents = Event.objects.filter(endDate__lt=datetime.datetime.today(), team__school__mentor__user=request.user).order_by('-startDate').distinct()

    # Invoices
    from invoices.models import Invoice
    try:
        invoices = Invoice.objects.filter(school__mentor__user=request.user)
    except ObjectDoesNotExist:
        print('user has no mentor')
        invoices = Invoice.objects.none()

    context = {
        'openForRegistrationEvents': openForRegistrationEvents,
        'currentEvents': currentEvents,
        'pastEvents': pastEvents,
        'invoices': invoices
    }
    return render(request, 'events/eventList.html', context)

@login_required
def detail(request, eventID):
    event = get_object_or_404(Event, pk=eventID)
    from teams.models import Team
    teams = Team.objects.filter(school__mentor__user=request.user, event__pk=eventID).prefetch_related('student_set')
    context = {
        'event': event,
        'teams': teams,
        'today':datetime.date.today()
    }
    return render(request, 'events/eventDetail.html', context)

@login_required
def summary(request, eventID):
    event = get_object_or_404(Event, pk=eventID)
    from teams.models import Team
    teams = Team.objects.filter(school__mentor__user=request.user, event__pk=eventID).prefetch_related('student_set')
    context = {
        'event': event,
        'teams': teams,
        'today':datetime.date.today()
    }
    return render(request, 'events/eventSummary.html', context)   

@login_required
def loggedInUnderConstruction(request):
    return render(request,'common/loggedInUnderConstruction.html') 

