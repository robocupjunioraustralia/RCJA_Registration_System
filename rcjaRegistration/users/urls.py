from django.urls import path

from . import views
app_name = 'users'
urlpatterns = [
    path('accounts/profile',views.editProfile, name="profile"),
]
