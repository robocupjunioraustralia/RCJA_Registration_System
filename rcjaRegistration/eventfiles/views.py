from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest, JsonResponse
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from coordination.permissions import checkCoordinatorPermission

# from .forms import 

from .models import MentorEventFileUpload, MentorEventFileType
from events.models import BaseEventAttendance

from events.views import mentorEventAttendanceAccessPermissions

from .forms import MentorEventFileUploadForm
from .s3_upload import (
    direct_s3_upload_enabled,
    generate_mentor_file_s3_key,
    generate_presigned_put_url,
    validate_upload_metadata,
    verify_s3_object,
)

import datetime
import json

def fileUploadCommonPermissions(request, eventAttendance):
    # Check event is published
    if not eventAttendance.event.published():
        raise PermissionDenied("Event is not published")

    # Check team - file upload currently not implemented for workshop attendees
    if not eventAttendance.eventAttendanceType() == 'team':
        raise PermissionDenied("File upload is only supported for teams") 

    if checkCoordinatorPermission(request, BaseEventAttendance, eventAttendance, 'change'):
        return

    # Check administrator of this eventAttendance
    if not mentorEventAttendanceAccessPermissions(request, eventAttendance):
        raise PermissionDenied("You are not an administrator of this team/ attendee")

def fileUploadEditPermissions(request, uploadedFile):
    fileUploadCommonPermissions(request, uploadedFile.eventAttendance)

    # Check upload deadline not passed
    if not uploadedFile.eventAttendance.event.eventavailablefiletype_set.filter(uploadDeadline__gte=datetime.datetime.today(), fileType=uploadedFile.fileType).exists():
        raise PermissionDenied("The upload deadline has passed for this file type for this event")

def fileUploadUploadPermissions( request, eventAttendance):
    fileUploadCommonPermissions(request, eventAttendance)

    # Check at least one available file type
    if not (eventAttendance.event.eventavailablefiletype_set.filter(uploadDeadline__gte=datetime.datetime.today()).exists()
        or checkCoordinatorPermission(request, BaseEventAttendance, eventAttendance, 'change')):
        raise PermissionDenied("File upload not available")

class MentorEventFileUploadView(LoginRequiredMixin, View):
    def admin_access(self, request, eventAttendance):
        return checkCoordinatorPermission(request, BaseEventAttendance, eventAttendance, 'change')

    def get_file_types(self, request, eventAttendance):
        if self.admin_access(request, eventAttendance):
            return eventAttendance.event.eventavailablefiletype_set.all()
        else:
            return eventAttendance.event.eventavailablefiletype_set.filter(uploadDeadline__gte=datetime.datetime.today())

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

        if mentorEventAttendanceAccessPermissions(request, eventAttendance):
            cancelURL = reverse('teams:details', kwargs = {"teamID": eventAttendance.id})
        else:
            cancelURL = reverse('admin:teams_team_changelist') + f"?event__id__exact={str(eventAttendance.event.id)}"

        return eventAttendance, uploadedFile, cancelURL

    def get(self, request, eventAttendanceID=None, uploadedFileID=None):
        # Get file and eventAttendance
        eventAttendance, uploadedFile, cancelURL = self.get_post_common(request, eventAttendanceID, uploadedFileID)

        context = {
            "eventAttendance": eventAttendance,
            "uploadedFile": uploadedFile,
            "availableFileUploadTypes": self.get_file_types(request, eventAttendance),
            "form": MentorEventFileUploadForm(instance=uploadedFile, uploadedFile=uploadedFile, eventAttendance=eventAttendance, admin=self.admin_access(request, eventAttendance)), # If uploadedFile is None this is simply passed to and dealt with by the Form - means uploading a new file
            "cancelURL": cancelURL,
            "directS3UploadEnabled": direct_s3_upload_enabled(),
        }

        return render(request, 'eventfiles/uploadMentorEventFile.html', context)

    def post(self, request, eventAttendanceID=None, uploadedFileID=None):
        # Get file and eventAttendance
        eventAttendance, uploadedFile, cancelURL = self.get_post_common(request, eventAttendanceID, uploadedFileID)

        if uploadedFile is None and direct_s3_upload_enabled() and request.POST.get('s3Key'):
            form = MentorEventFileUploadForm(instance=uploadedFile, uploadedFile=uploadedFile, eventAttendance=eventAttendance, admin=self.admin_access(request, eventAttendance))
            form.cleaned_data = {}
            s3_key = request.POST.get('s3Key', '').strip()
            original_filename = request.POST.get('originalFilename', '').strip()
            file_type_id = request.POST.get('fileType')

            try:
                if not s3_key or not original_filename or not file_type_id:
                    raise ValidationError('Missing required upload fields')

                if self.admin_access(request, eventAttendance):
                    file_type_queryset = MentorEventFileType.objects.all()
                else:
                    file_type_queryset = MentorEventFileType.objects.filter(
                        eventavailablefiletype__event__baseeventattendance=eventAttendance,
                        eventavailablefiletype__uploadDeadline__gte=datetime.datetime.today(),
                    )

                file_type = get_object_or_404(file_type_queryset, pk=file_type_id)
                verify_s3_object(s3_key, file_type)

                uploadedFile = MentorEventFileUpload(
                    eventAttendance=eventAttendance,
                    fileType=file_type,
                    uploadedBy=request.user,
                    originalFilename=original_filename,
                )
                uploadedFile.fileUpload.name = s3_key
                uploadedFile.full_clean()
                uploadedFile.save()

                if mentorEventAttendanceAccessPermissions(request, eventAttendance):
                    return redirect(reverse('teams:details', kwargs={"teamID": eventAttendance.id}))

                return redirect(reverse('admin:teams_team_changelist') + f"?event__id__exact={str(eventAttendance.event.id)}")
            except ValidationError as exc:
                if hasattr(exc, 'error_dict') and exc.error_dict:
                    for field, messages in exc.error_dict.items():
                        for message in messages:
                            form.add_error(field if field != '__all__' else None, message)
                elif hasattr(exc, 'messages'):
                    for message in exc.messages:
                        form.add_error(None, message)
                else:
                    form.add_error(None, str(exc))

            context = {
                "eventAttendance": eventAttendance,
                "uploadedFile": uploadedFile,
                "availableFileUploadTypes": self.get_file_types(request, eventAttendance),
                "form": form,
                "cancelURL": cancelURL,
                "directS3UploadEnabled": direct_s3_upload_enabled(),
            }

            return render(request, 'eventfiles/uploadMentorEventFile.html', context)

        # Get the form here so it can be used in the saving of valid data and also returning errors
        # If uploadedFile is None this is simply passed to and dealt with by the Form - means uploading a new file
        form = MentorEventFileUploadForm(request.POST, request.FILES, instance=uploadedFile, uploadedFile=uploadedFile, eventAttendance=eventAttendance, admin=self.admin_access(request, eventAttendance))

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

            # Redirect to team details view if admistrator of team, otherwise team admin changelist page
            if mentorEventAttendanceAccessPermissions(request, eventAttendance):
                return redirect(reverse('teams:details', kwargs = {"teamID": eventAttendance.id}))

            return redirect(reverse('admin:teams_team_changelist') + f"?event__id__exact={str(eventAttendance.event.id)}")

        # Default to displaying the form again if form not valid
        context = {
            "eventAttendance": eventAttendance,
            "uploadedFile": uploadedFile,
            "availableFileUploadTypes": self.get_file_types(request, eventAttendance),
            "form": form,
            "cancelURL": cancelURL,
            "directS3UploadEnabled": direct_s3_upload_enabled(),
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


class MentorEventFilePresignView(LoginRequiredMixin, View):
    def post(self, request, eventAttendanceID):
        if not direct_s3_upload_enabled():
            return HttpResponseBadRequest('Direct S3 upload is not enabled')

        eventAttendance = get_object_or_404(BaseEventAttendance, pk=eventAttendanceID)
        fileUploadUploadPermissions(request, eventAttendance)

        try:
            payload = json.loads(request.body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'errors': ['Invalid request body']}, status=400)

        original_filename = payload.get('originalFilename', '').strip()
        declared_size = payload.get('fileSize')
        content_type = payload.get('contentType', 'application/octet-stream').strip() or 'application/octet-stream'
        file_type_id = payload.get('fileType')

        if not original_filename or declared_size is None or not file_type_id:
            return JsonResponse({'errors': ['Missing required fields']}, status=400)

        try:
            declared_size = int(declared_size)
        except (TypeError, ValueError):
            return JsonResponse({'errors': ['Invalid file size']}, status=400)

        admin_access = checkCoordinatorPermission(request, BaseEventAttendance, eventAttendance, 'change')
        if admin_access:
            file_type_queryset = MentorEventFileType.objects.all()
        else:
            file_type_queryset = MentorEventFileType.objects.filter(
                eventavailablefiletype__event__baseeventattendance=eventAttendance,
                eventavailablefiletype__uploadDeadline__gte=datetime.datetime.today(),
            )

        file_type = get_object_or_404(file_type_queryset, pk=file_type_id)

        try:
            validate_upload_metadata(file_type, original_filename, declared_size)
            s3_key = generate_mentor_file_s3_key(original_filename)
            presigned_url = generate_presigned_put_url(s3_key, content_type)
        except ValidationError as exc:
            if hasattr(exc, 'messages'):
                errors = [str(message) for message in exc.messages]
            else:
                errors = [str(exc)]
            return JsonResponse({'errors': errors}, status=400)

        return JsonResponse({'presignedUrl': presigned_url, 's3Key': s3_key})
