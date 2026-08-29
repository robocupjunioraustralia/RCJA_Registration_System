from django import forms
from django.forms import ModelForm

import datetime

from .models import MentorEventFileUpload, MentorEventFileType
from .helpers import validFileTypes

class MentorEventFileUploadForm(ModelForm):
    class Meta:
        model = MentorEventFileUpload
        fields = [
            'fileUpload',
            'fileType',
        ]

    # Override init to filter fileType
    def __init__(self, *args, uploadedFile, eventAttendance, isCoordinator=False, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter fileType to available fileTypes
        self.fields['fileType'].queryset = validFileTypes(isCoordinator, eventAttendance)

        if uploadedFile:
            self.fields['fileUpload'].disabled = True
