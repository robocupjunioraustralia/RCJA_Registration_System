from django.shortcuts import render
from common.views import *

from .serializers import *

from events.models import Event
from regions.models import State, Region

# *****Regions*****

# class StateViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = State.objects.order_by('id')
#     serializer_class = StateSerializer

# class RegionViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = Region.objects.order_by('id')
#     serializer_class = RegionSerializer

# # *****Events*****

# class EventViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = Event.objects.order_by('id')
#     serializer_class = EventSerializer
