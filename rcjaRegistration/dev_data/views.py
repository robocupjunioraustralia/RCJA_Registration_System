from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from coordination.permissions import checkCoordinatorPermission

import datetime

from eventfiles.models import MentorEventFileType, EventAvailableFileType
from events.models import DivisionCategory, Division,AvailableDivision, Event, BaseEventAttendance, Year, Venue
from invoices.models import InvoiceGlobalSettings
from regions.models import State, Region
from teams.models import Team, Student, PlatformCategory, HardwarePlatform, SoftwarePlatform
from schools.models import Campus
from workshops.models import WorkshopAttendee
from userquestions.models import Question

@login_required
def download(request):
    data = {"Metadata":{"date": datetime.date.today()}}
    # No data removal necessary 
    models = [MentorEventFileType, EventAvailableFileType, DivisionCategory, Division, Year, AvailableDivision, InvoiceGlobalSettings, State, Region, PlatformCategory, HardwarePlatform, SoftwarePlatform, Question]
    for model in models:
        if model.objects.exists():
            allObjects = []
            for object in model.objects.all() :
                variables = vars(object)
                variables.pop('_state')
                variables.pop('creationDateTime')
                variables.pop('updatedDateTime')
                
                allObjects.append(variables)
            data[model.__name__] = allObjects

    # Data removal
    if Venue.objects.exists():
        venues = []
        for object in Venue.objects.all() :
            variables = vars(object)
            variables.pop('_state')
            variables.pop('creationDateTime')
            variables.pop('updatedDateTime')
            variables['venueImage'] = None
            variables['address'] = ""
            venues.append(variables)
        data[Venue.__name__] = venues

    if Event.objects.exists():
        events = []
        for object in Event.objects.all() :
            variables = vars(object)
            variables.pop('_state')
            variables.pop('creationDateTime')
            variables.pop('updatedDateTime')
            variables.pop('directEnquiriesTo_id')
            events.append(variables)
        data[Event.__name__] = events

    return JsonResponse(data)

def upload(request):
    pass
    
