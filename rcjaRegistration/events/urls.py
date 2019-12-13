from django.urls import path

from . import views

app_name = 'events'
urlpatterns = [
    path('events/', views.index, name='list'),
    path('events/<int:eventID>', views.detail, name='detail')
]
