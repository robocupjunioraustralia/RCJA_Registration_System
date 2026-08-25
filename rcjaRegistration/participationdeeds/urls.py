from django.urls import path
from . import views

app_name = 'participationdeeds'

urlpatterns = [
    path('participation-deeds/sign/<str:token>/', views.sign_participation_deed, name='sign_participation_deed'),
    path('events/<int:eventID>/participation-deeds/mentor/', views.mentor_summary, name='mentor_summary'),
    path(
        'events/<int:eventID>/participation-deeds/attach/<int:deedID>/',
        views.attach_deed_view,
        name='attach',
    ),
    path('events/<int:eventID>/participation-deeds/', views.coordinator_summary, name='coordinator_summary'),
]
