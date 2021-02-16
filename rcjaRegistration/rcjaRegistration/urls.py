"""rcjaRegistration URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.views.generic.base import RedirectView
from django.contrib.auth import views as auth_views
from .forms import CustomAuthForm

admin.site.site_header = "RCJA Admin"
admin.site.site_title = "RCJA Admin"
admin.site.index_title = "Administration Home"


urlpatterns = [
    path('admin/', admin.site.urls),
    # Authentication urls and overrides
    # Static must be hosted on different domain for redirect_authenticated_user to be secure
    # This is done in production as everything is stored in S3
    # See https://docs.djangoproject.com/en/3.1/topics/auth/default/#all-authentication-views
    path('accounts/login/', auth_views.LoginView.as_view(authentication_form=CustomAuthForm, redirect_authenticated_user=True), name='login'),
    # Login user after password reset and redirect to the password change done page, which uses the logged in base template
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(post_reset_login=True, success_url=reverse_lazy('password_change_done')), name='password_reset_confirm'),
    path('accounts/', include('django.contrib.auth.urls')),

    # Project urls
    path('api/v1/public/', include('publicapi.urls')),
    path('', include('events.urls')),
    path('',include('schools.urls')),
    path('',include('teams.urls')),
    path('',include('workshops.urls')),
    path('',include('users.urls')),
    path('',include('invoices.urls')),
    path('',include('eventfiles.urls')),
    path('',include('regions.urls')),
]
