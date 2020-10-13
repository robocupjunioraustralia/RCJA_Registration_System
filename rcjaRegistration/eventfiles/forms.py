from django import forms
from django.forms import ModelForm

import datetime

from .models import MentorEventFileUpload, MentorEventFileType

class MentorEventFileUploadForm(ModelForm):
    class Meta:
        model = MentorEventFileUpload
        fields = [
            'fileUpload',
            'fileType',
            'comments',
        ]

    # Override init to filter fileType
    def __init__(self, *args, uploadedFile, eventAttendance, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter fileType to available fileTypes
        self.fields['fileType'].queryset = MentorEventFileType.objects.filter(eventavailablefiletype__event__baseeventattendance=eventAttendance, eventavailablefiletype__uploadDeadline__gte=datetime.datetime.today())

        if uploadedFile:
            self.fields['fileUpload'].disabled = True
