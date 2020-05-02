from django.urls import path

from . import views
app_name = 'workshops'
urlpatterns = [
    path('workshops/create/<int:eventID>', views.CreateEditWorkshopAttendee.as_view(), name='create'),
    path('workshops/<int:attendeeID>', views.CreateEditWorkshopAttendee.as_view(), name='details')
]
