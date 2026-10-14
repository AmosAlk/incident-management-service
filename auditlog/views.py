from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from auditlog.models import AuditEvent
from auditlog.serializers import AuditEventSerializer
from incidents.models import Incident


class IncidentAuditEventListView(generics.ListAPIView):
    serializer_class = AuditEventSerializer
    permission_classes = [IsAuthenticated]

    def get_incident(self) -> Incident:
        return get_object_or_404(
            Incident.objects.filter(
                organisation__memberships__user=self.request.user
            ).distinct(),
            pk=self.kwargs["incident_id"],
        )

    def get_queryset(self):
        incident = self.get_incident()

        return AuditEvent.objects.filter(
            organisation=incident.organisation,
            resource_type=AuditEvent.ResourceType.INCIDENT,
            resource_id=incident.id,
        ).select_related("actor")
