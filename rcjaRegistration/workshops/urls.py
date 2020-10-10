from django.urls import path

from . import views
app_name = 'workshops'
urlpatterns = [
    path('workshopattendee/create/<int:eventID>', views.CreateEditWorkshopAttendee.as_view(), name='create'),
    path('workshopattendee/<int:attendeeID>', views.CreateEditWorkshopAttendee.as_view(), name='details')
]
