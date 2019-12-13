from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.http import HttpResponse
from django.template import loader

import datetime

from .models import Competition

# Need to check if mentor is None

def index(request):
    openForRegistrationCompetitions = Competition.objects.filter(registrationsOpenDate__lte=datetime.datetime.today(), registrationsCloseDate__gte=datetime.datetime.today()).exclude(team__school__mentor__user=request.user).order_by('startDate')
    currentCompetitions = Competition.objects.filter(endDate__gte=datetime.datetime.today(), team__school__mentor__user=request.user).distinct().order_by('startDate')
    pastCompetitions = Competition.objects.filter(endDate__lt=datetime.datetime.today(), team__school__mentor__user=request.user).order_by('-startDate')
    context = {
        'openForRegistrationCompetitions': openForRegistrationCompetitions,
        'currentCompetitions': currentCompetitions,
        'pastCompetitions': pastCompetitions
    }
    return render(request, 'competitions/viewcomp.html', context)

def detail(request, competitionID):
    competition = get_object_or_404(Competition, pk=competitionID)
    from teams.models import Team
    teams = Team.objects.filter(school__mentor__user=request.user, competition__pk=competitionID).prefetch_related('student_set')
    context = {
        'competition': competition,
        'teams': teams
    }
    return render(request, 'competitions/compDetail.html', context)
