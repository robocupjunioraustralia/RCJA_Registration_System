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
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.contrib.auth import views as auth_views
from .forms import CustomAuthForm

admin.site.site_header = "RCJA Admin"
admin.site.site_title = "RCJA Admin"
admin.site.index_title = "Administration Home"


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(authentication_form=CustomAuthForm)),
    path('accounts/', include('django.contrib.auth.urls')), #login
    path('api/v1/public/', include('publicapi.urls')),
    path('', include('events.urls')),
    path('',include('schools.urls')),
    path('',include('teams.urls')),
    path('',include('workshops.urls')),
    path('',include('users.urls')),
    path('',include('invoices.urls')),
    path('',include('eventfiles.urls')),
    # path('',RedirectView.as_view(url='/events/dashboard', permanent=False), name='index'),   
]
