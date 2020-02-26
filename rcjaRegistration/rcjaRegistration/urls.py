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

admin.site.site_header = "RCJA Admin"
admin.site.site_title = "RCJA Admin Portal"
admin.site.index_title = "Welcome to the RCJA Admin Portal"


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')), #login
    # path('api/v1/', include('apiv1.urls')), # Disabled for initial release
    path('', include('events.urls')),
    path('',include('schools.urls')),
    path('',include('teams.urls')),
    path('',include('users.urls')),
    path('',include('invoices.urls')),
    path('',RedirectView.as_view(url='/events/dashboard', permanent=False), name='index')
    
]