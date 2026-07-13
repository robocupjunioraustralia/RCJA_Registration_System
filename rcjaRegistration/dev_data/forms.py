from django import forms

from events.models import Division, Year
from schools.models import Campus
from events.models import AvailableDivision

class DownloadDataForm(forms.Form):
    deleteData = forms.BooleanField(required=False, label="Delete")
    data_to_upload = forms.JSONField(required=False)