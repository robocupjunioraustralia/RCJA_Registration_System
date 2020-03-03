from django.urls import path

from . import views
app_name = 'teams'
urlpatterns = [
    path('events/<int:eventID>/createTeam', views.createTeam, name='create'),
    path('teams/<int:teamID>/delete', views.deleteTeam, name='delete'),
    path('teams/<int:teamID>/edit', views.editTeam, name='edit')
]
