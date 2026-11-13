from typing import cast
from unittest.mock import patch

import pytest
from celery.contrib.django.task import DjangoTask
from django.contrib.auth.models import User
from django.core import mail
from django.test import override_settings
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from incidents.models import Incident
from incidents.tasks import (
    notify_administrators_incident_created,
)
from organisations.models import (
    Organisation,
    OrganisationMembership,
)


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND=("django.core.mail.backends.locmem.EmailBackend"))
def test_incident_notification_is_sent_to_administrator() -> None:
    administrator = User.objects.create_user(
        username="alice",
        email="alice@example.test",
    )

    creator = User.objects.create_user(
        username="bob",
    )

    organisation = Organisation.objects.create(
        name="Acme Security AB",
    )

    OrganisationMembership.objects.create(
        organisation=organisation,
        user=administrator,
        role=OrganisationMembership.Role.ADMINISTRATOR,
    )

    OrganisationMembership.objects.create(
        organisation=organisation,
        user=creator,
        role=OrganisationMembership.Role.ANALYST,
    )

    incident = Incident.objects.create(
        organisation=organisation,
        title="Suspicious authentication",
        description="Unexpected authentication activity.",
        severity=Incident.Severity.HIGH,
        created_by=creator,
    )
    # Pylance fix here again
    cast(DjangoTask, notify_administrators_incident_created).run(str(incident.pk))

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["alice@example.test"]
    assert incident.title in mail.outbox[0].subject


@pytest.mark.django_db
@patch("incidents.views.notify_administrators_incident_created.delay_on_commit")
def test_incident_creation_schedules_notification(
    mock_delay_on_commit,
) -> None:
    analyst = User.objects.create_user(
        username="alice",
    )

    organisation = Organisation.objects.create(
        name="Acme Security AB",
    )

    OrganisationMembership.objects.create(
        organisation=organisation,
        user=analyst,
        role=OrganisationMembership.Role.ANALYST,
    )

    client = APIClient()
    client.force_authenticate(user=analyst)

    response = client.post(
        reverse("incidents:list-create"),
        {
            "organisation": str(organisation.pk),
            "title": "Suspicious authentication",
            "description": "Unexpected login activity.",
            "severity": Incident.Severity.HIGH,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED

    incident = Incident.objects.get(pk=response.data["id"])

    mock_delay_on_commit.assert_called_once_with(str(incident.pk))
