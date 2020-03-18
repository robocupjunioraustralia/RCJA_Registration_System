from django.urls import path

from . import views
app_name = 'teams'
urlpatterns = [
    path('teams/create/<int:eventID>', views.Create.as_view(), name='create'),
    path('teams/<int:teamID>', views.Details.as_view(), name='details')
]
