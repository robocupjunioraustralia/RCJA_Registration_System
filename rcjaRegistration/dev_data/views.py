from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.views.defaults import page_not_found

from django.db import connection

import datetime, re

from association.models import AssociationMember
from coordination.models import Coordinator
from eventfiles.models import (
    MentorEventFileType,
    EventAvailableFileType,
    MentorEventFileUpload,
)
from events.models import (
    DivisionCategory,
    Division,
    AvailableDivision,
    Event,
    BaseEventAttendance,
    Year,
    Venue,
)
from invoices.models import InvoiceGlobalSettings, Invoice, InvoicePayment
from regions.models import State, Region
from teams.models import (
    Team,
    Student,
    PlatformCategory,
    HardwarePlatform,
    SoftwarePlatform,
    Team,
)
from schools.models import Campus, School, SchoolAdministrator
from workshops.models import WorkshopAttendee
from userquestions.models import Question, QuestionResponse
from users.models import User

from .forms import DownloadDataForm

"""
A list of all models in order of dependency. Later tables reference earlier 
tables. The remove dictionary allows specific information to be set to a 
specific value, instead of the current setting when downloading. The download 
field states whether the model should be converted to JSON data
"""
models = [
    {"class": InvoiceGlobalSettings, "remove": {}, "download": True},
    {
        "class": Year,
        "remove": {},
        "download": True,
    },
    {
        "class": State,
        "remove": {
            "defaultEventImage": None,
            "bankAccountName": None,
            "bankAccountBSB": None,
            "bankAccountNumber": None,
            "paypalEmail": "",
        },
        "download": True,
    },
    {"class": Region, "remove": {}, "download": True},
    {"class": School, "remove": {}, "download": False},
    {"class": Campus, "remove": {}, "download": False},
    {"class": Venue, "remove": {"venueImage": None, "address": ""}, "download": True},
    {"class": DivisionCategory, "remove": {}, "download": True},
    {"class": Division, "remove": {}, "download": True},
    {"class": PlatformCategory, "remove": {}, "download": True},
    {"class": HardwarePlatform, "remove": {}, "download": True},
    {"class": SoftwarePlatform, "remove": {}, "download": True},
    {"class": User, "remove": {}, "download": False},
    {"class": SchoolAdministrator, "remove": {}, "download": False},
    {"class": AssociationMember, "remove": {}, "download": False},
    {"class": Coordinator, "remove": {}, "download": False},
    {"class": Question, "remove": {}, "download": True},
    {"class": QuestionResponse, "remove": {}, "download": False},
    {
        "class": Event,
        "remove": {"eventBannerImage": "", "directEnquiriesTo_id": 1},
        "download": True,
    },
    {"class": AvailableDivision, "remove": {}, "download": True},
    {"class": BaseEventAttendance, "remove": {}, "download": False},
    {"class": MentorEventFileType, "remove": {}, "download": True},
    {"class": Invoice, "remove": {}, "download": False},
    {"class": MentorEventFileUpload, "remove": {}, "download": False},
    {"class": EventAvailableFileType, "remove": {}, "download": True},
    {"class": InvoicePayment, "remove": {}, "download": False},
    {"class": WorkshopAttendee, "remove": {}, "download": False},
    {"class": Team, "remove": {}, "download": False},
    {"class": Student, "remove": {}, "download": False},
]  # Not including Users


@login_required
def download(request):
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to view this page")
    data = {"Metadata": {"date": datetime.date.today()}}
    # No data removal necessary
    for model in models:
        if model["class"].objects.exists() and model["download"]:
            allObjects = []  # All objects for particular class
            for object in model["class"].objects.all():
                variables = vars(object)  # Copy all attributes
                variables.pop("_state")  # Remove meta variables
                variables.pop("creationDateTime")
                variables.pop("updatedDateTime")
                # Apply replacements
                for field, replacement in model["remove"].items():
                    variables[field] = replacement
                allObjects.append(variables)
            # Add data to list
            data[model["class"].__name__] = allObjects
    return JsonResponse(data)


def deleteData(request):
    if not request.user.is_superuser:  # Double check
        return
    for model in models[::-1]:  # Delete everything in reverse order
        model["class"].objects.all().delete()


def uploadData(data):
    today = datetime.date.today()
    for model in models:  # Iterate through all given models
        if model["class"].__name__ in data:
            for object in data[
                model["class"].__name__
            ]:  # Iterate through data for model
                for key in object:
                    if isinstance(object[key], str) and re.search(
                        "2[0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]", object[key]
                    ):  # Replace dates time shifted to current
                        object[key] = (
                            datetime.date.fromisoformat(object[key])
                            - datetime.date.fromisoformat(data["Metadata"]["date"])
                            + today
                        )
                    elif re.search(r"\w*_id", key):
                        match key:
                            case "directEnquiriesTo_id":  # To avoid bad references
                                object[key] = User.objects.all().first().pk
                model["class"].objects.create(**object)
        elif model["class"] == User:  # Always ensure one user for enquires
            # Details shouldn't matter as on development
            User.objects.create_superuser(email="tester@test.com", password="test")


@login_required
def upload(request):
    if settings.ENVIRONMENT != "development":
        return page_not_found(request, None)
    if not request.user.is_staff:
        return page_not_found(request, None)
    if not settings.DEBUG:
        return page_not_found(request, None)

    if request.method == "POST":
        form = DownloadDataForm(request.POST)
        if form.is_valid():
            if form.cleaned_data["deleteData"]:
                deleteData(request)
            if form.cleaned_data["data_to_upload"]:
                uploadData(form.cleaned_data["data_to_upload"])
    else:
        form = DownloadDataForm()
    context = {
        "form": form,
    }
    return render(request, "dev_data/upload.html", context)
