from django.shortcuts import render, get_object_or_404
from django.db.models import F, Q
from django.core.exceptions import ValidationError
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models.deletion import ProtectedError

from common.apiPermissions import CmsSecretPermission

from events.models import Event

class CMSIntegrationViewSet(viewsets.ViewSet):
    permission_classes = [CmsSecretPermission]

    @action(detail=False, methods=["POST"])
    def linkEvent(self, request):
        """
        Expects:
          - eventId (the ID of the event in Rego)
          - cmsEventId (the ID of the event in the CMS)

        Updates the Event's cmsEventId field (only for competitions)
        """
        event_id = request.data.get("eventId")
        cms_event_id = request.data.get("cmsEventId")

        if not (event_id and cms_event_id):
            return Response(
                {"detail": "Both 'eventId' and 'cmsEventId' are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        event = get_object_or_404(Event, pk=event_id)

        if event.eventType != "competition":
            return Response(
                {"detail": "cmsEventId can only be set for competitions."},
                status=status.HTTP_400_BAD_REQUEST
            )

        event.cmsEventId = cms_event_id
        event.save()

        return Response(
            {"detail": f"Successfully linked '{cms_event_id}' to '{event}'."},
            status=status.HTTP_200_OK
        )
