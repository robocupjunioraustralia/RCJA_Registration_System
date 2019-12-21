from django.shortcuts import render, get_object_or_404,redirect

# Create your views here.
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth.decorators import login_required

from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
import datetime

from .models import Competition

# Need to check if mentor is None

@login_required
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

@login_required
def detail(request, competitionID):
    competition = get_object_or_404(Competition, pk=competitionID)
    from teams.models import Team
    teams = Team.objects.filter(school__mentor__user=request.user, competition__pk=competitionID).prefetch_related('student_set')
    context = {
        'competition': competition,
        'teams': teams
    }
    return render(request, 'competitions/compDetail.html', context)

