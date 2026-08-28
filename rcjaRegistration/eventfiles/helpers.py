from coordination.permissions import checkCoordinatorPermission
from events.models import BaseEventAttendance
from .models import MentorEventFileType

import datetime

def getIsCoordinator(request, eventAttendance):
    return checkCoordinatorPermission(request, BaseEventAttendance, eventAttendance, 'change')

def availableFileUploadTypes(isCoordinator, eventAttendance):
    if isCoordinator:
        return eventAttendance.event.eventavailablefiletype_set.all()
    else:
        return eventAttendance.event.eventavailablefiletype_set.filter(uploadDeadline__gte=datetime.datetime.today())

def availableFileUploadTypes_req(request, eventAttendance):
    return availableFileUploadTypes(getIsCoordinator(request, eventAttendance), eventAttendance)

def validFileTypes(isCoordinator, eventAttendance):
    return MentorEventFileType.objects.filter(pk__in=availableFileUploadTypes(isCoordinator, eventAttendance).values_list('pk', flat=True))

def validFileTypes_req(request, eventAttendance):
    return validFileTypes(getIsCoordinator(request, eventAttendance), eventAttendance)
