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

# *****Regions*****

class StateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = State.objects.order_by('id')
    serializer_class = StateSerializer

    permission_classes = (ReadOnly,)

    @action(detail=True)
    def events(self, request, pk=None):
        queryset = Event.objects.filter(state__pk=pk).order_by('id')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = EventSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = EventSerializer(queryset, many=True)
        return Response(serializer.data)
