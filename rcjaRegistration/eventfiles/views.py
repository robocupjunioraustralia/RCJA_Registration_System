from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

# from .forms import 

from .models import MentorEventFileUpload
from events.models import BaseEventAttendance

from events.views import mentorEventAttendanceAccessPermissions

from .forms import MentorEventFileUploadForm

import datetime

def fileUploadCommonPermissions(request, eventAttendance):
    # Check event is published
    if not eventAttendance.event.published():
        raise PermissionDenied("Event is not published")

    # Check administrator of this eventAttendance
    if not mentorEventAttendanceAccessPermissions(request, eventAttendance):
        raise PermissionDenied("You are not an administrator of this team/ attendee")

    # Check team - file upload currently not implemented for workshop attendees
    if not eventAttendance.eventAttendanceType() == 'team':
        raise PermissionDenied("File upload is only supported for teams") 

def fileUploadEditPermissions(request, uploadedFile):
    fileUploadCommonPermissions(request, uploadedFile.eventAttendance)

    # Check upload deadline not passed
    if not uploadedFile.eventAttendance.event.eventavailablefiletype_set.filter(uploadDeadline__gte=datetime.datetime.today(), fileType=uploadedFile.fileType).exists():
        raise PermissionDenied("The upload deadline has passed for this file type for this event")

def fileUploadUploadPermissions( request, eventAttendance):
    fileUploadCommonPermissions(request, eventAttendance)

    # Check at least one available file type
    if not eventAttendance.event.eventavailablefiletype_set.filter(uploadDeadline__gte=datetime.datetime.today()).exists():
        raise PermissionDenied("File upload not available")

class MentorEventFileUploadView(LoginRequiredMixin, View):
    def get_post_common(self, request, eventAttendanceID, uploadedFileID):
        # Check if editing an existing file
        if uploadedFileID is not None:
            # Get file
            uploadedFile = get_object_or_404(MentorEventFileUpload, pk=uploadedFileID)

            # Check edit permissions
            fileUploadEditPermissions(request, uploadedFile)

            # Get eventAttendance for this file
            eventAttendance = uploadedFile.eventAttendance
        else:
            # Otherwise assume uploading a new file - is the only alternative and in the event that this is also None, will just return 404
            # Get eventAttendance object
            eventAttendance = get_object_or_404(BaseEventAttendance, pk=eventAttendanceID)

            # Check upload permissions
            fileUploadUploadPermissions(request, eventAttendance)

            # No existing file so set to None
            uploadedFile = None

        return eventAttendance, uploadedFile

    def get(self, request, eventAttendanceID=None, uploadedFileID=None):
        # Get file and eventAttendance
        eventAttendance, uploadedFile = self.get_post_common(request, eventAttendanceID, uploadedFileID)

        context = {
            "eventAttendance": eventAttendance,
            "uploadedFile": uploadedFile,
            "availableFileUploadTypes": eventAttendance.event.eventavailablefiletype_set.filter(uploadDeadline__gte=datetime.datetime.today()),
            "form": MentorEventFileUploadForm(instance=uploadedFile, uploadedFile=uploadedFile, eventAttendance=eventAttendance), # If uploadedFile is None this is simply passed to and dealt with by the Form - means uploading a new file
        }

        return render(request, 'eventfiles/uploadMentorEventFile.html', context)

    def post(self, request, eventAttendanceID=None, uploadedFileID=None):
        # Get file and eventAttendance
        eventAttendance, uploadedFile = self.get_post_common(request, eventAttendanceID, uploadedFileID)

        # Get the form here so it can be used in the saving of valid data and also returning errors
        # If uploadedFile is None this is simply passed to and dealt with by the Form - means uploading a new file
        form = MentorEventFileUploadForm(request.POST, request.FILES, instance=uploadedFile, uploadedFile=uploadedFile, eventAttendance=eventAttendance)

        if form.is_valid():
            # Create fileUpload object but don't save so can set foreign keys
            uploadedFile = form.save(commit=False)

            # Set the eventAttendance - is not present on the form
            uploadedFile.eventAttendance = eventAttendance

            # Set the uploadedBy field only if no PK - which means new file
            if not uploadedFile.pk:
                uploadedFile.uploadedBy = request.user

            # Save uploadedFile
            uploadedFile.save()

            # Redirect to team details view
            return redirect(reverse('teams:details', kwargs = {"teamID": eventAttendance.id}))

        # Default to displaying the form again if form not valid
        context = {
            "eventAttendance": eventAttendance,
            "uploadedFile": uploadedFile,
            "availableFileUploadTypes": eventAttendance.event.eventavailablefiletype_set.filter(uploadDeadline__gte=datetime.datetime.today()),
            "form": form,
        }

        return render(request, 'eventfiles/uploadMentorEventFile.html', context)

    def delete(self, request, eventAttendanceID=None, uploadedFileID=None):
        # This endpoint should never be called with eventAttendanceID
        if eventAttendanceID is not None:
            return HttpResponseForbidden()

        # Get uploadedFile object
        uploadedFile = get_object_or_404(MentorEventFileUpload, pk=uploadedFileID)

        # Check permissions
        fileUploadEditPermissions(request, uploadedFile)

        # Delete team
        uploadedFile.delete()
        return HttpResponse(status=204)
