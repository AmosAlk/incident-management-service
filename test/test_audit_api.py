import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from auditlog.models import AuditEvent
from incidents.models import Incident
from organisations.models import Organisation, OrganisationMembership


@pytest.mark.django_db
def test_incident_creation_generates_audit_event() -> None:
    user = User.objects.create_user(username="alice", password="test")

    organisation = Organisation.objects.create(
        name="Acme Security AB",
    )

    OrganisationMembership.objects.create(
        organisation=organisation,
        user=user,
        role=OrganisationMembership.Role.ANALYST,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        reverse("incidents:list-create"),
        {
            "organisation": str(organisation.id),
            "title": "Suspicious login",
            "description": "An unusual login was detected.",
            "severity": Incident.Severity.HIGH,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED

    incident = Incident.objects.get()
    event = AuditEvent.objects.get()

    assert event.actor == user
    assert event.organisation == organisation
    assert event.action == AuditEvent.Action.INCIDENT_CREATED
    assert event.resource_id == incident.id


@pytest.mark.django_db
def test_status_change_generates_audit_event() -> None:
    user = User.objects.create_user(
        username="alice",
        password="test",
    )

    organisation = Organisation.objects.create(
        name="Acme Security AB",
    )

    OrganisationMembership.objects.create(
        organisation=organisation,
        user=user,
        role=OrganisationMembership.Role.ANALYST,
    )

    incident = Incident.objects.create(
        organisation=organisation,
        title="Suspicious login",
        description="An unusual login was detected.",
        severity=Incident.Severity.HIGH,
        created_by=user,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.patch(
        reverse(
            "incidents:detail",
            kwargs={"pk": incident.id},
        ),
        {
            "status": Incident.Status.INVESTIGATING,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    event = AuditEvent.objects.get()

    assert event.action == AuditEvent.Action.INCIDENT_STATUS_CHANGED
    assert event.metadata == {
        "old_status": "open",
        "new_status": "investigating",
    }


@pytest.mark.django_db
def test_user_can_list_audit_events_for_their_incident() -> None:
    user = User.objects.create_user(
        username="alice",
        password="test",
    )

    organisation = Organisation.objects.create(
        name="Acme Security AB",
    )

    OrganisationMembership.objects.create(
        organisation=organisation,
        user=user,
        role=OrganisationMembership.Role.VIEWER,
    )

    incident = Incident.objects.create(
        organisation=organisation,
        title="Suspicious login",
        description="An unusual login was detected.",
        severity=Incident.Severity.HIGH,
        created_by=user,
    )

    AuditEvent.objects.create(
        organisation=organisation,
        actor=user,
        action=AuditEvent.Action.INCIDENT_CREATED,
        resource_type=AuditEvent.ResourceType.INCIDENT,
        resource_id=incident.id,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(
        reverse(
            "incidents:audit-event-list",
            kwargs={"incident_id": incident.id},
        )
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["action"] == "incident.created"


@pytest.mark.django_db
def test_user_cannot_read_another_organisations_audit_events() -> None:
    alice = User.objects.create_user(
        username="alice",
        password="test",
    )

    bob = User.objects.create_user(
        username="bob",
        password="test",
    )

    acme = Organisation.objects.create(
        name="Acme Security AB",
    )

    northstar = Organisation.objects.create(
        name="Northstar Systems AB",
    )

    OrganisationMembership.objects.create(
        organisation=acme,
        user=alice,
        role=OrganisationMembership.Role.ANALYST,
    )

    incident = Incident.objects.create(
        organisation=northstar,
        title="Northstar incident",
        description="Private incident.",
        severity=Incident.Severity.HIGH,
        created_by=bob,
    )

    AuditEvent.objects.create(
        organisation=northstar,
        actor=bob,
        action=AuditEvent.Action.INCIDENT_CREATED,
        resource_type=AuditEvent.ResourceType.INCIDENT,
        resource_id=incident.id,
    )

    client = APIClient()
    client.force_authenticate(user=alice)

    response = client.get(
        reverse(
            "incidents:audit-event-list",
            kwargs={"incident_id": incident.id},
        )
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
