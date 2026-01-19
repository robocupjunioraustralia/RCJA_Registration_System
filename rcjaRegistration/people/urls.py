from django.urls import path
from .views import getStudents, searchStudents

app_name = 'students'

urlpatterns = [
    path('students/autocomplete', getStudents, name='studentAutocomplete'),
    path('students/get', searchStudents, name='studentSearch'),
]
