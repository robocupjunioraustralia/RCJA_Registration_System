from django.urls import path

from . import views
app_name = 'teams'
urlpatterns = [
    path('events/<int:eventID>/createTeam', views.CreateTeam.as_view(), name='create'),
    path('teams/<int:teamID>/delete', views.deleteTeam, name='delete'),
    path('teams/<int:teamID>/edit', views.EditTeam.as_view(), name='edit')
]
