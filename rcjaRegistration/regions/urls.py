from django.urls import path
from django.conf.urls import url

from . import views

app_name = 'regions'

urlpatterns = [
    url(r'^regions/region-autocomplete/$', views.RegionAutocomplete.as_view(), name='region-autocomplete'),
]
