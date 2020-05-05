from django.shortcuts import render, get_object_or_404

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

class NestedSerializerActionMinxin:
    def nestedSerializer(self, queryset, serializerClass):
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializerClass(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = serializerClass(queryset, many=True)
        return Response(serializer.data)

# *****Regions*****

class StateViewSet(viewsets.ReadOnlyModelViewSet, NestedSerializerActionMinxin):
    queryset = State.objects.filter(typeWebsite=True).order_by('id')
    serializer_class = StateSerializer

    permission_classes = (ReadOnly,)

    def eventsBaseQueryset(self, pk):
        state = get_object_or_404(State, pk=pk)
        if state.typeGlobal:
            return Event.objects.filter(globalEvent=True, status='published')
        else:
            return Event.objects.filter(globalEvent=False, state=state, status='published')

    @action(detail=True)
    def upcomingEvents(self, request, pk=None):
        queryset = self.eventsBaseQueryset(pk).filter(startDate__gte=datetime.datetime.today()).order_by('startDate')
        return self.nestedSerializer(queryset, EventSerializer)

    @action(detail=True)
    def pastEvents(self, request, pk=None):
        # May want to limit the past events that are available
        queryset = self.eventsBaseQueryset(pk).filter(startDate__lt=datetime.datetime.today()).order_by('-startDate')
        return self.nestedSerializer(queryset, EventSerializer)
