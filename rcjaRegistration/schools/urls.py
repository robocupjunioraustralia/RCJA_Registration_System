from django.urls import path

from . import views
app_name = 'schools'
urlpatterns = [
    path('schools/mentorRegistration',views.mentorRegistration),
    path('schools/schoolCreation',views.schoolCreation)
]



