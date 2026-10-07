from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from incidents.models import Incident
from incidents.permissions import CanModifyIncident
from incidents.serializers import IncidentSerializer, IncidentUpdateSerializer
from organisations.models import OrganisationMembership


@api_view(["GET"])
def health_check(_request: Request) -> Response:
    """Report that the HTTP application is running."""
    return Response({"status": "ok"})


# Retrieve several objects OR create one.
class IncidentListCreateView(generics.ListCreateAPIView):
    # https://www.cdrf.co/3.13/rest_framework.generics/ListCreateAPIView.html
    # Internal properties of ListCreateAPIView that we are modifying.
    # permission_classes needs to specify which serializer to use.
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated]

    # A queryset is a django representation of a database query returning
    # model objects.
    def get_queryset(self):
        return (
            Incident.objects.filter(
                # Utilises our organisation "related name" to find its
                # memberships. Essentially traverses from each incident,
                # to its organisation, to the memberships belonging to
                # that organisation, and returns those where the correct
                # user has a membership to that organisation.
                organisation__memberships__user=self.request.user
            )
            # All fields from foreign keys are fetched in the same query,
            # rather than with additional queries afterward.
            # More efficient.
            .select_related(
                "organisation",
                "created_by",
                "assigned_to",
            )
            # Technically not needed here since we have a uniqueness constraint
            # on the user already, but if we were to query with multiple users
            # at the same time then this would be needed as the join could
            # give us the same incident several times.
            .distinct()
        )

    def perform_create(self, serializer):
        # At this point, the IncidentSerializer has already validated
        # and converted incoming data and stores it in validated_data.
        # We then extract the organisation object from that dictionary.
        organisation = serializer.validated_data["organisation"]

        membership = OrganisationMembership.objects.filter(
            organisation=organisation,
            user=self.request.user,
        ).first()

        if membership is None:
            raise PermissionDenied("You are not a member of this organisation.")

        allowed_roles = {
            OrganisationMembership.Role.ADMINISTRATOR,
            OrganisationMembership.Role.ANALYST,
        }

        if membership.role not in allowed_roles:
            raise PermissionDenied("Your role cannot create incidents.")

        # Use the validated data to create an incident object, with
        # the created_by field as the logged in user. We want to
        # guarantee this is correct so we set it ourselves.
        serializer.save(created_by=self.request.user)


# Since the retrieved UUID is called pk, DRF can automatically
# pass it to IncidentDetailView from incidents/urls.py/
class IncidentDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = IncidentUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        CanModifyIncident,
    ]
    http_method_names = [
        "get",
        "patch",
        "head",
        "options",
    ]

    def get_queryset(self):
        return (
            Incident.objects.filter(organisation__memberships__user=self.request.user)
            .select_related(
                "organisation",
                "created_by",
                "assigned_to",
            )
            .distinct()
        )
