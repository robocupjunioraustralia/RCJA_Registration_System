from django.db import models
from common.models import *
from django.conf import settings

from django.utils.html import format_html
from common.utils import formatFilesize
from common.fields import UUIDFileField

from events.models import eventCoordinatorViewPermissions

from rcjaRegistration.storageBackends import PrivateMediaStorage

# **********MODELS**********

class MentorEventFileType(models.Model):
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)

    # Fields
    name = models.CharField('Name', max_length=60, unique=True)
    description = models.CharField('Description', max_length=200, blank=True)
    systemMaxFileSizeMB = 1000
    maxFilesizeMB = models.PositiveIntegerField('Max file size (MB)', default=100)
    allowedFileTypes = models.CharField('Allowed file types', max_length=200, help_text='Comma separated list allowed file types, leave blank for no restrictions', blank=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = "Mentor Event File Type"

    def clean(self):
        errors = []

        if self.maxFilesizeMB > MentorEventFileType.systemMaxFileSizeMB:
            errors.append(ValidationError("Max file size exceeds maximum allowed (1000MB)"))

        # Raise any errors
        if errors:
            raise ValidationError(errors)

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        # Only superusers can edit file type
        return eventCoordinatorViewPermissions(level)

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return self.name

    # *****CSV export methods*****

    # *****Email methods*****


class MentorEventFileUpload(models.Model):
    # Foreign keys
    eventAttendance = models.ForeignKey('events.BaseEventAttendance', verbose_name='Team/ attendee', on_delete=models.CASCADE)
    uploadedBy = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Uploaded by', on_delete=models.PROTECT, editable=False)
    fileType = models.ForeignKey('eventfiles.MentorEventFileType', verbose_name='Type', on_delete=models.PROTECT)

    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)

    # Fields
    comments = models.TextField('Comments', blank=True)

    # File
    fileUpload = UUIDFileField('File', storage=PrivateMediaStorage(), upload_prefix="MentorFile", original_filename_field="originalFileName")
    originalFileName = models.CharField('Original filename', max_length=300, editable=False)

    # *****Meta and clean*****
    class Meta:
        verbose_name = "Mentor Event File Upload"


    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        # May want to make this editable by admin, or at least creatable
        return eventCoordinatorViewPermissions(level)

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return f"{str(self.eventAttendance)} {self.creationDateTime}"

    def event(self):
        return self.eventAttendance.event
    event.short_description = 'Event'
    event.admin_order_field = 'eventAttendance__event'

    # File methods

    def filesize(self):
        return formatFilesize(self.fileUpload.size)
    filesize.short_description = 'Size'

    # *****CSV export methods*****

    # *****Email methods*****

