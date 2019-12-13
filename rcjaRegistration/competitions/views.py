from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.template import loader

from .models import Competition


def index(request):
    competitions = Competition.objects.order_by('startDate')
    template = loader.get_template('competitions/viewcomp.html')
    context = {
        'comps': competitions,
    }
    return HttpResponse(template.render(context, request))
