from django.urls import path

from . import views
app_name = 'competitions'
urlpatterns = [
    path('competitions/', views.index, name='list'),
    path('competitions/<int:competitionID>', views.detail, name='detail'),
]
