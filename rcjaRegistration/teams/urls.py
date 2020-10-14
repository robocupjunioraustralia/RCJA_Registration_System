from django.urls import path

from . import views
app_name = 'teams'
urlpatterns = [
    path('teams/create/<int:eventID>', views.CreateEditTeam.as_view(), name='create'),
    path('teams/<int:teamID>/edit', views.CreateEditTeam.as_view(), name='edit'),
    path('teams/<int:teamID>', views.details, name='details'),
]
