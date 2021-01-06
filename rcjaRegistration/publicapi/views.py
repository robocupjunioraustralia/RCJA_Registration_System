from django.shortcuts import render, get_object_or_404

from django.core.exceptions import ValidationError
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models.deletion import ProtectedError

from common.apiPermissions import ReadOnly

from .serializers import StateSerializer, EventSerializer

from events.models import Event
from regions.models import State
# from publicwebsite.models import CommitteeMember

import datetime

class NestedSerializerActionMinxin:
    def nestedSerializer(self, queryset, serializerClass):
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializerClass(page, many=True, context={'request': self.request})
            return self.get_paginated_response(serializer.data)

        serializer = serializerClass(queryset, many=True, context={'request': self.request})
        return Response(serializer.data)

# *****Regions*****

class StateViewSet(viewsets.ReadOnlyModelViewSet, NestedSerializerActionMinxin):
    lookup_field = 'abbreviation'
    queryset = State.objects.filter(typeWebsite=True).order_by('id')
    serializer_class = StateSerializer

    permission_classes = (ReadOnly,)

    def eventsBaseQueryset(self, abbreviation):
        state = get_object_or_404(State, abbreviation=abbreviation, typeWebsite=True)
        if state.typeGlobal:
            return Event.objects.filter(globalEvent=True, status='published')
        else:
            return Event.objects.filter(globalEvent=False, state=state, status='published')

    @action(detail=True)
    def upcomingEvents(self, request, abbreviation=None):
        queryset = self.eventsBaseQueryset(abbreviation).filter(startDate__gte=datetime.datetime.today()).order_by('startDate')
        return self.nestedSerializer(queryset, EventSerializer)

    @action(detail=True)
    def pastEvents(self, request, abbreviation=None):
        # May want to limit the past events that are available
        queryset = self.eventsBaseQueryset(abbreviation).filter(startDate__lt=datetime.datetime.today()).order_by('-startDate')
        return self.nestedSerializer(queryset, EventSerializer)

    # @action(detail=True)
    # def committeeMembers(self, request, pk=None):
    #     state = get_object_or_404(State, pk=pk, typeWebsite=True)
    #     queryset = CommitteeMember.objects.filter(state=state).order_by('id')
    #     return self.nestedSerializer(queryset, CommitteeMemberSerializer)
