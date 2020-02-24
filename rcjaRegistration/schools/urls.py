from django.urls import path

from . import views
app_name = 'schools'
urlpatterns = [
    path('schools/setCurrentSchool/<int:schoolID>', views.setCurrentSchool, name='setCurrentSchool'),
    # path('schools/createSchool', views.schoolCreation, name='createSchool'),
    path('schools/profile', views.details, name='details'),
    path('accounts/signup', views.signup, name="signup"),
    path('schools/createSchoolAJAX', views.createSchoolAJAX, name="createAJAX")
]
