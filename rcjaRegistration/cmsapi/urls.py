from django.contrib import admin
from django.urls import path, include
from django.urls import re_path

from rest_framework import routers

from . import views

from common.apiPermissions import CmsSecretPermission

# **********Routers**********

Router = routers.DefaultRouter()
Router.get_api_root_view().cls.permission_classes = (CmsSecretPermission,)

# # *****CMS*****
Router.register(r'integration', views.CMSIntegrationViewSet, basename='cms')

# # **********URL patterns**********

app_name = 'cmsapiv1'
urlpatterns = [
    re_path(r'', include(Router.urls)),
]
