from django.contrib import admin
from django.urls import path, include
from django.conf.urls import url

from rest_framework import routers

from . import views

from common.apiPermissions import ReadOnly

# **********Routers**********

Router = routers.DefaultRouter()
Router.get_api_root_view().cls.permission_classes = (ReadOnly,)

# # *****Regions*****

Router.register(r'states', views.StateViewSet)

# # *****Events*****

# # **********URL patterns**********

app_name = 'apiv1'
urlpatterns = [
    url(r'', include(Router.urls)),
]
