from django.urls import path

from . import views
app_name = 'teams'
urlpatterns = [
    path('events/<int:eventID>/createTeam/', views.createTeam, name='create'),
    path('teams/delete/<int:teamID>/', views.deleteTeam, name='delete'),
    path('teams/edit/<int:teamID>/', views.editTeam, name='edit')
]
