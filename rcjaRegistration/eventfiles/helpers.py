from coordination.permissions import checkCoordinatorPermission
from events.models import BaseEventAttendance

import datetime

def getIsCoordinator(request, eventAttendance):
    return checkCoordinatorPermission(request, BaseEventAttendance, eventAttendance, 'change')

def form_availableFileUploadTypes(isCoordinator, eventAttendance):
    if isCoordinator:
        return eventAttendance.event.eventavailablefiletype_set.all()
    else:
        return eventAttendance.event.eventavailablefiletype_set.filter(uploadDeadline__gte=datetime.datetime.today())

def availableFileUploadTypes(request, eventAttendance):
    return form_availableFileUploadTypes(getIsCoordinator(request, eventAttendance), eventAttendance)
