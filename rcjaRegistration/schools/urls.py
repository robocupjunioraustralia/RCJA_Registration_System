from django.urls import path

from . import views
app_name = 'schools'
urlpatterns = [
    path('schools/setCurrentSchool/<int:schoolID>', views.setCurrentSchool, name='setCurrentSchool'),
    path('schools/create', views.create, name='create'),
    path('schools/profile', views.details, name='details'),
    path('schools/admin/merge/<int:school1ID>/<int:school2ID>', views.adminMergeSchools, name='adminMergeSchools'),
]
