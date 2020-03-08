from django.contrib import admin
from django.urls import path, include
from django.conf.urls import url

from rest_framework import routers

from . import views


# **********Routers**********

# Router = routers.DefaultRouter()

# # *****Regions*****

# Router.register(r'states',views.StateViewSet)
# Router.register(r'regions',views.RegionViewSet)

# # *****Events*****

# Router.register(r'events',views.EventViewSet)


# # **********URL patterns**********

# app_name = 'apiv1'
# urlpatterns = [
#     url(r'', include(Router.urls)),
# ]
