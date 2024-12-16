from os import environ 
from django.shortcuts import render as django_render

def render(request, template_name, context=None, *args, **kwargs):
    if type(context) == dict:
        context["development"] = environ["DEV_SETTINGS"]
    else:
        context = {"development":environ["DEV_SETTINGS"]}
    return django_render(request, template_name, context, *args, **kwargs)