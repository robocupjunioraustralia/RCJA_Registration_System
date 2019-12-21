from django.db import models
from django.forms import ModelForm
from .models import Mentor, School

class MentorForm(ModelForm):
    class Meta:
        model = Mentor
        fields = ['school', 'mobile_phone_number']
class SchoolForm(ModelForm):
    class Meta:
        model = School
        fields = ['name','abbreviation','region']