from django.urls import path
from .views import getStudents, searchStudents, manageStudents, archiveStudents

app_name = "students"

urlpatterns = [
    path("students/autocomplete", getStudents, name="studentAutocomplete"),
    path("students/get", searchStudents, name="studentSearch"),
    path("students/manageStudents", manageStudents, name="manageStudents"),
    path("students/archive", archiveStudents, name="archiveStudents"),
]
