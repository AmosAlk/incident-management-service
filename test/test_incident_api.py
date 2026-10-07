import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from incidents.models import Incident
from organisations.models import Organisation, OrganisationMembership


@pytest.mark.django_db
def test_analyst_can_create_incident() -> None:
    user = get_user_model().objects.create_user(
        username="alice",
    )
    organisation = Organisation.objects.create(
        name="Acme Security AB",
    )
    OrganisationMembership.objects.create(
        organisation=organisation,
        user=user,
        role=OrganisationMembership.Role.ANALYST,
    )

    # Better suited for REST API testing than just Client
    client = APIClient()
    # This is not an authentication test, so we eliminate everything
    # not strictly necessary for this test.
    client.force_authenticate(user=user)

    response = client.post(
        # Describes the endpoint named list-create from incidents.
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

    assert incident.created_by == user
    assert incident.organisation == organisation
    assert incident.status == Incident.Status.OPEN


@pytest.mark.django_db
def test_viewer_cannot_create_incident() -> None:
    user = get_user_model().objects.create_user(
        username="viewer",
    )
    organisation = Organisation.objects.create(
        name="Acme Security AB",
    )
    OrganisationMembership.objects.create(
        organisation=organisation,
        user=user,
        role=OrganisationMembership.Role.VIEWER,
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

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Incident.objects.count() == 0


@pytest.mark.django_db
def test_user_only_lists_incidents_from_their_organisation() -> None:
    user = get_user_model().objects.create_user(
        username="alice",
    )

    acme = Organisation.objects.create(
        name="Acme Security AB",
    )
    northstar = Organisation.objects.create(
        name="Northstar Systems AB",
    )

    OrganisationMembership.objects.create(
        organisation=acme,
        user=user,
        role=OrganisationMembership.Role.ANALYST,
    )

    acme_incident = Incident.objects.create(
        organisation=acme,
        title="Acme incident",
        description="Visible to Alice.",
        severity=Incident.Severity.MEDIUM,
        created_by=user,
    )

    other_user = get_user_model().objects.create_user(
        username="bob",
    )

    northstar_incident = Incident.objects.create(
        organisation=northstar,
        title="Northstar incident",
        description="Must not be visible to Alice.",
        severity=Incident.Severity.HIGH,
        created_by=other_user,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(reverse("incidents:list-create"))

    assert response.status_code == status.HTTP_200_OK

    returned_ids = {item["id"] for item in response.data}

    assert str(acme_incident.id) in returned_ids
    assert str(northstar_incident.id) not in returned_ids


@pytest.mark.django_db
def test_user_cannot_retrieve_incident_from_another_organisation() -> None:
    alice = get_user_model().objects.create_user(
        username="alice",
    )
    bob = get_user_model().objects.create_user(
        username="bob",
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
        title="Private Northstar incident",
        description="Alice must not see this.",
        severity=Incident.Severity.CRITICAL,
        created_by=bob,
    )

    client = APIClient()
    client.force_authenticate(user=alice)

    response = client.get(
        reverse(
            "incidents:detail",
            kwargs={"pk": incident.id},
        )
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_analyst_can_update_incident() -> None:
    user = get_user_model().objects.create_user(
        username="alice",
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

    # Must be loaded from db after to see the change, may not be recorded
    # in memory.
    incident.refresh_from_db()

    assert incident.status == Incident.Status.INVESTIGATING


@pytest.mark.django_db
def test_viewer_cannot_update_incident() -> None:
    viewer = get_user_model().objects.create_user(
        username="viewer",
    )
    creator = get_user_model().objects.create_user(
        username="creator",
    )
    organisation = Organisation.objects.create(
        name="Acme Security AB",
    )

    OrganisationMembership.objects.create(
        organisation=organisation,
        user=viewer,
        role=OrganisationMembership.Role.VIEWER,
    )

    incident = Incident.objects.create(
        organisation=organisation,
        title="Suspicious login",
        description="An unusual login was detected.",
        severity=Incident.Severity.HIGH,
        created_by=creator,
    )

    client = APIClient()
    client.force_authenticate(user=viewer)

    response = client.patch(
        reverse(
            "incidents:detail",
            kwargs={"pk": incident.id},
        ),
        {
            "severity": Incident.Severity.CRITICAL,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN

    incident.refresh_from_db()

    assert incident.severity == Incident.Severity.HIGH


@pytest.mark.django_db
def test_incident_cannot_skip_from_open_to_closed() -> None:
    user = get_user_model().objects.create_user(
        username="alice",
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
            "status": Incident.Status.CLOSED,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    incident.refresh_from_db()

    assert incident.status == Incident.Status.OPEN


@pytest.mark.django_db
def test_incident_cannot_be_assigned_to_user_from_another_organisation() -> None:
    alice = get_user_model().objects.create_user(
        username="alice",
    )
    bob = get_user_model().objects.create_user(
        username="bob",
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

    OrganisationMembership.objects.create(
        organisation=northstar,
        user=bob,
        role=OrganisationMembership.Role.ANALYST,
    )

    incident = Incident.objects.create(
        organisation=acme,
        title="Suspicious login",
        description="An unusual login was detected.",
        severity=Incident.Severity.HIGH,
        created_by=alice,
    )

    client = APIClient()
    client.force_authenticate(user=alice)

    response = client.patch(
        reverse(
            "incidents:detail",
            kwargs={"pk": incident.id},
        ),
        {
            "assigned_to": bob.id,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    incident.refresh_from_db()

    assert incident.assigned_to is None
