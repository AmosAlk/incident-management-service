import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from incidents.models import Incident
from organisations.models import Organisation, OrganisationMembership


# Regression test of read only fields when creating incidents
# after introducing keycloak.
@pytest.mark.django_db
def test_incident_creation_ignores_server_controlled_fields() -> None:
    analyst = User.objects.create_user(
        username="analyst",
    )
    victim = User.objects.create_user(
        username="victim",
    )

    organisation = Organisation.objects.create(
        name="Acme Security AB",
    )

    OrganisationMembership.objects.create(
        organisation=organisation,
        user=analyst,
        role=OrganisationMembership.Role.ANALYST,
    )

    OrganisationMembership.objects.create(
        organisation=organisation,
        user=victim,
        role=OrganisationMembership.Role.ANALYST,
    )

    client = APIClient()
    client.force_authenticate(user=analyst)

    response = client.post(
        reverse("incidents:list-create"),
        {
            "organisation": str(organisation.pk),
            "title": "Suspicious login",
            "description": "Unexpected authentication activity.",
            "severity": Incident.Severity.HIGH,
            "status": Incident.Status.CLOSED,
            "created_by": victim.pk,
            "assigned_to": victim.pk,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED

    incident = Incident.objects.get(pk=response.data["id"])

    # These are all read only fields, so the serializer ignores any
    # attempt att changing these, and they will have assigned
    # values by the server.
    assert incident.created_by == analyst
    assert incident.status == Incident.Status.OPEN
    assert incident.assigned_to is None
