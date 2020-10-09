from django.db import models
from common.models import *
from django.conf import settings

import uuid
from django.utils.html import format_html
from common.utils import formatFilesize

from rcjaRegistration.storageBackends import PrivateMediaStorage

# **********MODELS**********

class MentorEventAttendanceFile(models.Model):
    # Foreign keys
    eventAttendance = models.ForeignKey('events.BaseEventAttendance', verbose_name='Event Attendance', on_delete=models.PROTECT) # Not sure how to handle deletions. Ideally need to delete the file in S3.
    uploadedBy = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Uploaded by', on_delete=models.PROTECT, editable=False)

    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)

    # Fields

    # Banner image
    def generateUUIDFilename(self, filename):
        self.originalFileName = filename
        extension = filename.rsplit('.', 1)[1]
        newFilename = f'MentorFile_{str(uuid.uuid4())}.{extension}'
        return newFilename
    fileUpload = models.ImageField('File', storage=PrivateMediaStorage(), upload_to=generateUUIDFilename)
    originalFileName = models.CharField('Original filename', max_length=300, editable=False)

    # *****Meta and clean*****
    class Meta:
        verbose_name = "Mentor Event File"


    # *****Permissions*****
    # @classmethod
    # def coordinatorPermissions(cls, level):
    #     return eventCoordinatorViewPermissions(level)

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        attendanceChildObject = self.eventAttendance.childObject()

        return f"{str(attendanceChildObject)} {self.creationDateTime}"

    def filesize(self):
        return formatFilesize(self.fileUpload.size)
    filesize.short_description = 'Size'

    # *****CSV export methods*****

    # *****Email methods*****

