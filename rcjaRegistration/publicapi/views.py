from django.shortcuts import render

from django.core.exceptions import ValidationError
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models.deletion import ProtectedError

from common.apiPermissions import ReadOnly

from .serializers import *

from events.models import Event
from regions.models import State, Region

import datetime

# *****Regions*****

class StateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = State.objects.order_by('id')
    serializer_class = StateSerializer

    permission_classes = (ReadOnly,)

    @action(detail=True)
    def upcomingEvents(self, request, pk=None):
        queryset = Event.objects.filter(state__pk=pk, status='published', startDate__gte=datetime.datetime.today()).order_by('startDate')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = EventSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = EventSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True)
    def pastEvents(self, request, pk=None):
        # May want to limit the past events that are available
        queryset = Event.objects.filter(state__pk=pk, status='published', startDate__lt=datetime.datetime.today()).order_by('-startDate')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = EventSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = EventSerializer(queryset, many=True)
        return Response(serializer.data)
