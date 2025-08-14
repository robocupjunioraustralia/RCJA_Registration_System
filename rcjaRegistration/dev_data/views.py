from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.conf import settings

import datetime, re

from association.models import AssociationMember
from coordination.models import Coordinator
from eventfiles.models import MentorEventFileType, EventAvailableFileType, MentorEventFileUpload
from events.models import DivisionCategory, Division,AvailableDivision, Event, BaseEventAttendance, Year, Venue
from invoices.models import InvoiceGlobalSettings, Invoice, InvoicePayment
from regions.models import State, Region
from teams.models import Team, Student, PlatformCategory, HardwarePlatform, SoftwarePlatform, Team
from schools.models import Campus, School, SchoolAdministrator
from workshops.models import WorkshopAttendee
from userquestions.models import Question, QuestionResponse
from users.models import User, UserManager

from .forms import DownloadDataForm

models = [
    {"class":InvoiceGlobalSettings,"remove":{},"download":True},
    {"class":Year,"remove":{},"download":True}, 
    {"class":State,"remove":{},"download":True}, 
    {"class":Region,"remove":{},"download":True}, 
    {"class":School,"remove":{},"download":False},
    {"class":Campus,"remove":{},"download":False},
    {"class":Venue,"remove":{'venueImage': None,'address':""},"download":True}, 
    {"class":DivisionCategory,"remove":{},"download":True}, 
    {"class":Division,"remove":{},"download":True}, 
    {"class":PlatformCategory,"remove":{},"download":True}, 
    {"class":HardwarePlatform,"remove":{},"download":True}, 
    {"class":SoftwarePlatform,"remove":{},"download":True},
    {"class":User,"remove":{},"download":False},
    {"class":SchoolAdministrator,"remove":{},"download":False},
    {"class":AssociationMember,"remove":{},"download":False},
    {"class":Coordinator,"remove":{},"download":False},
    {"class":Question,"remove":{},"download":True},
    {"class":QuestionResponse,"remove":{},"download":False},
    {"class":Event,"remove":{'directEnquiriesTo_id':1},"download":True}, 
    {"class":AvailableDivision,"remove":{},"download":True}, 
    {"class":BaseEventAttendance,"remove":{},"download":False},
    {"class":MentorEventFileType,"remove":{},"download":True}, 
    {"class":Invoice,"remove":{},"download":False},
    {"class":MentorEventFileUpload,"remove":{},"download":False},
    {"class":EventAvailableFileType,"remove":{},"download":True},
    {"class":InvoicePayment,"remove":{},"download":False},
    {"class":WorkshopAttendee,"remove":{},"download":False},
    {"class":Team,"remove":{},"download":False},
    {"class":Student,"remove":{},"download":False},
] # Not including Users

@login_required
def download(request):
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to view this page")
    data = {"Metadata":{"date": datetime.date.today()}}
    # No data removal necessary 
    for model in models:
        if model["class"].objects.exists() and model["download"]:
            allObjects = []
            for object in model["class"].objects.all() :
                variables = vars(object)
                variables.pop('_state')
                variables.pop('creationDateTime')
                variables.pop('updatedDateTime')

                for field, replacement in model["remove"].items():
                    variables[field] = replacement
                allObjects.append(variables)
            data[model["class"].__name__] = allObjects
    return JsonResponse(data)

def deleteData():
    print("DELETING DATA")
    for model in models[::-1]:
        model["class"].objects.all().delete()

def uploadData(data):
    today = datetime.date.today()
    for model in models:
        if model["class"].__name__ in data:
            for object in data[model["class"].__name__]:
                for key in object:
                    print(key, isinstance(object[key],str), bool(re.search(r"\w*_id",key)))
                    if isinstance(object[key],str) and re.search("2[0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]",object[key]):
                        object[key] = datetime.date.fromisoformat(object[key]) \
                            -datetime.date.fromisoformat(data["Metadata"]["date"]) \
                            + today
                    elif re.search(r"\w*_id",key):
                        print("ID")
                        match key:
                            case "directEnquiriesTo_id":
                                object[key]=User.objects.all().first().pk
                                print("FOUND")
                model["class"].objects.create(**object)
        elif model["class"] == User:
            User.objects.create_superuser(email="tester@test.com",password="test")

@login_required
def upload(request):
    if (not request.user.is_staff):
        raise PermissionDenied("You do not have permission to view this page.")
    if (not settings.DEV_SETTINGS):
        raise SuspiciousOperation("You are not allowed to upload data to a production server.")
    if request.method == 'POST':
        form = DownloadDataForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['deleteData']:
                deleteData()
            if form.cleaned_data['data_to_upload']:
                uploadData(form.cleaned_data['data_to_upload'])
    else:
        form = DownloadDataForm()
    context = {
        "form": form,
    }
    return render(request, 'dev_data/upload.html', context)