from django.db import models
from common.models import *
from django.conf import settings

from django.utils.html import format_html
from common.utils import formatFilesize
from common.fields import UUIDFileField

from rcjaRegistration.storageBackends import PrivateMediaStorage

# **********MODELS**********

class MentorEventFileUpload(SaveDeleteMixin, models.Model):
    # Foreign keys
    eventAttendance = models.ForeignKey('events.BaseEventAttendance', verbose_name='Team/ attendee', on_delete=models.CASCADE)
    uploadedBy = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Uploaded by', on_delete=models.PROTECT, editable=False)

    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)

    # Fields

    # File
    fileUpload = UUIDFileField('File', storage=PrivateMediaStorage(), upload_prefix="MentorFile", original_filename_field="originalFileName")
    originalFileName = models.CharField('Original filename', max_length=300, editable=False)

    # *****Meta and clean*****
    class Meta:
        verbose_name = "Mentor Event File Upload"


    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        from events.models import eventCoordinatorViewPermissions
        return eventCoordinatorViewPermissions(level)

    # *****Save & Delete Methods*****

    # Need to handle bulk delete!!
    def postDelete(self):
        # Delete the actual file
        self.fileUpload.delete(save=False)

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

