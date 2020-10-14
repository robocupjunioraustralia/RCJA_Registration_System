from django.db import models
from common.models import SaveDeleteMixin, checkRequiredFieldsNotNone
from django.core.exceptions import ValidationError
from django.conf import settings

import datetime

from django.utils.html import format_html
from django.template.defaultfilters import filesizeformat
from common.fields import UUIDFileField

from events.models import eventCoordinatorViewPermissions, eventCoordinatorEditPermissions

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
        ordering = ['name']

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

    def maxFileSizeStr(self):
        return filesizeformat(self.maxFilesizeBytes())
    maxFileSizeStr.short_description = 'Max size'

    def maxFilesizeBytes(self):
        return self.maxFilesizeMB * 2**20

    def __str__(self):
        return self.name

    # *****CSV export methods*****

    # *****Email methods*****

class EventAvailableFileType(models.Model):
    # Foreign keys
    event = models.ForeignKey('events.Event', verbose_name='Event', on_delete=models.CASCADE)
    fileType = models.ForeignKey('eventfiles.MentorEventFileType', verbose_name='Type', on_delete=models.PROTECT)

    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)

    # Fields
    uploadDeadline = models.DateField('Upload deadline')

    # *****Meta and clean*****
    class Meta:
        verbose_name = "Event Available File Type"
        unique_together = ('event', 'fileType')
        ordering = ['event', 'fileType']

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        # Only superusers can edit file type
        return eventCoordinatorEditPermissions(level)

    # Used in state coordinator permission checking
    def getState(self):
        return self.event.state

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return f"{self.event}: {self.fileType}"

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
    fileUpload = UUIDFileField('File', storage=PrivateMediaStorage(), upload_prefix="MentorFile", original_filename_field="originalFilename")
    originalFilename = models.CharField('Original filename', max_length=300, editable=False)

    # *****Meta and clean*****
    class Meta:
        verbose_name = "Mentor Event File Upload"
        ordering = ['eventAttendance', 'fileType']

    def clean(self):
        errors = []
        # Check required fields are not None
        checkRequiredFieldsNotNone(self, ['fileType', 'fileUpload'])

        # Check allowed file extension
        # Empty list means no restriction
        try:
            extension = self.fileUpload.name.rsplit('.', 1)[1]
        except IndexError:
            raise ValidationError("File must have a file extension")
        if self.fileType.allowedFileTypes and extension not in self.fileType.allowedFileTypes:
            errors.append(ValidationError(f'File not of allowed type, must be: {self.fileType.allowedFileTypes}'))

        # Check within size limit
        if self.fileUpload.size > self.fileType.maxFilesizeBytes():
            errors.append(ValidationError(f'File must be less than {filesizeformat(self.fileType.maxFilesizeBytes())}. Current filesize is {filesizeformat(self.fileUpload.size)}.'))

        # Raise any errors
        if errors:
            raise ValidationError(errors)

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        # May want to make this editable by admin, or at least creatable
        return eventCoordinatorEditPermissions(level)

    # Used in state coordinator permission checking
    def getState(self):
        return self.eventAttendance.event.state


    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return f"{self.originalFilename}"

    def event(self):
        return self.eventAttendance.event
    event.short_description = 'Event'
    event.admin_order_field = 'eventAttendance__event'

    # File methods

    def filesize(self):
        return filesizeformat(self.fileUpload.size)
    filesize.short_description = 'Size'

    def fileURL(self):
        return self.fileUpload.url
    fileURL.short_description = 'URL'

    def uploadDeadlinePassed(self):
        return not self.eventAttendance.event.eventavailablefiletype_set.filter(uploadDeadline__gte=datetime.datetime.today(), fileType=self.fileType).exists()

    # *****CSV export methods*****

    # *****Email methods*****

