from django.urls import path

from . import views
app_name = 'userprofiles'
urlpatterns = [
    path('accounts/profile',views.editProfile, name="profile"),
]
