from django.contrib import admin
from django.urls import path, include
from django.urls import re_path

from rest_framework import routers

from . import views

from common.apiPermissions import CmsSecretPermission

# **********Routers**********

Router = routers.SimpleRouter()

# # *****CMS*****
Router.register(r'integration', views.CMSIntegrationViewSet, basename='cms')

# # **********URL patterns**********

app_name = 'cmsapiv1'
urlpatterns = [
    re_path(r'', include(Router.urls)),
]
