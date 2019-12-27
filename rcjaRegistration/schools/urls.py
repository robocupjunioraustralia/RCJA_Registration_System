from django.urls import path

from . import views
app_name = 'schools'
urlpatterns = [
    path('schools/createSchool',views.schoolCreation,name='createSchool'),
    path('accounts/signup',views.signup,name="signup")
]
