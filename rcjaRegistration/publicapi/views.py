from django.shortcuts import render

from django.core.exceptions import ValidationError
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from rest_framework import status, viewsets
from rest_framework.response import Response

from django.db.models.deletion import ProtectedError

from .serializers import *

from events.models import Event
from regions.models import State, Region

# *****Regions*****

class StateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = State.objects.order_by('id')
    serializer_class = StateSerializer

# *****Events*****

class EventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Event.objects.order_by('id')
    serializer_class = EventSerializer
