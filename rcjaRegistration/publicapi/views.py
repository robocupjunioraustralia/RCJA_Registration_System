from django.shortcuts import render, get_object_or_404

from django.core.exceptions import ValidationError
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models.deletion import ProtectedError

from common.apiPermissions import ReadOnly

from .serializers import StateSerializer, EventSerializer, SummaryEventSerializer

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
    lookup_field = 'abbreviation__iexact'
    lookup_url_kwarg = 'abbreviation'
    queryset = State.objects.filter(typeWebsite=True).order_by('id')
    serializer_class = StateSerializer

    permission_classes = (ReadOnly,)

    def eventsBaseQueryset(self, abbreviation):
        state = get_object_or_404(State, abbreviation__iexact=abbreviation, typeWebsite=True)
        if state.typeGlobal:
            return Event.objects.filter(globalEvent=True, status='published', year__displayEventsOnWebsite=True)
        else:
            return Event.objects.filter(globalEvent=False, state=state, status='published', year__displayEventsOnWebsite=True)

    def upcomingEventsQueryset(self, abbreviation):
        return self.eventsBaseQueryset(abbreviation).filter(startDate__gte=datetime.datetime.today()).order_by('startDate')
    
    def pastEventsQueryset(self, abbreviation):
        return self.eventsBaseQueryset(abbreviation).filter(startDate__lt=datetime.datetime.today()).order_by('-startDate')

    # Summary event endpoint
    # Returns all events (past and upcoming) from years with displayEventsOnWebsite=True
    # Includes all published competitions and workshops
    # Fewer fields returned, uses summary serializer
    @action(detail=True)
    def allEvents(self, request, abbreviation=None):
        queryset = self.eventsBaseQueryset(abbreviation).order_by('startDate')
        return self.nestedSerializer(queryset, SummaryEventSerializer)

    # Upcoming events

    @action(detail=True)
    def upcomingEvents(self, request, abbreviation=None):
        queryset = self.upcomingEventsQueryset(abbreviation)
        return self.nestedSerializer(queryset, EventSerializer)

    @action(detail=True)
    def upcomingCompetitions(self, request, abbreviation=None):
        queryset = self.upcomingEventsQueryset(abbreviation).filter(eventType = 'competition')
        return self.nestedSerializer(queryset, EventSerializer)

    @action(detail=True)
    def upcomingWorkshops(self, request, abbreviation=None):
        queryset = self.upcomingEventsQueryset(abbreviation).filter(eventType = 'workshop')
        return self.nestedSerializer(queryset, EventSerializer)

    # Past events

    @action(detail=True)
    def pastEvents(self, request, abbreviation=None):
        queryset = self.pastEventsQueryset(abbreviation)
        return self.nestedSerializer(queryset, EventSerializer)

    @action(detail=True)
    def pastCompetitions(self, request, abbreviation=None):
        queryset = self.pastEventsQueryset(abbreviation).filter(eventType = 'competition')
        return self.nestedSerializer(queryset, EventSerializer)

    @action(detail=True)
    def pastWorkshops(self, request, abbreviation=None):
        queryset = self.pastEventsQueryset(abbreviation).filter(eventType = 'workshop')
        return self.nestedSerializer(queryset, EventSerializer)

    # @action(detail=True)
    # def committeeMembers(self, request, pk=None):
    #     state = get_object_or_404(State, pk=pk, typeWebsite=True)
    #     queryset = CommitteeMember.objects.filter(state=state).order_by('id')
    #     return self.nestedSerializer(queryset, CommitteeMemberSerializer)
