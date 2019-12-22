from django.db import models
from django.forms import ModelForm
from .models import Mentor, School

class MentorForm(ModelForm):
    class Meta:
        model = Mentor
        fields = ['school', 'mobileNumber']
class SchoolForm(ModelForm):
    class Meta:
        model = School
        fields = ['name','abbreviation','region','state']