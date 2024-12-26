from os import environ 
from django.conf import settings
from django.shortcuts import render as django_render

def render(request, template_name, context=None, *args, **kwargs):
    """ Add tag to header depending on environment """
    if settings.ENVIRONMENT == "production":
        environment = None
    else:
        environment = settings.ENVIRONMENT.upper()
    if type(context) == dict:
        context["environment"] = environment
    else:
        context = {"environment": environment}
    return django_render(request, template_name, context, *args, **kwargs)