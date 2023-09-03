from django.urls import path

from . import views
app_name = 'users'
urlpatterns = [
    path('accounts/profile',views.details, name="details"),
    path('accounts/signup', views.signup, name="signup"),
    path('termsAndConditions', views.termsAndConditions, name="termsAndConditions"),
    path('dashboard/setCurrentAdminYear/<int:year>', views.setCurrentAdminYear, name='setCurrentAdminYear'),
    path('dashboard/setCurrentAdminState/<int:stateID>', views.setCurrentAdminState, name='setCurrentAdminState'),
]
