from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from config.throttling import (
    BurstRateThrottle,
    WriteRateThrottle,
)
from incidents.models import Incident
from organisations.models import Organisation, OrganisationMembership


@pytest.mark.django_db
@patch.object(
    BurstRateThrottle,
    "rate",
    "2/min",
    create=True,
)
def test_burst_throttle_returns_429() -> None:
    cache.clear()

    user = User.objects.create_user(
        username="alice",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    url = reverse("incidents:list-create")

    first_response = client.get(url)
    second_response = client.get(url)
    third_response = client.get(url)

    assert first_response.status_code == status.HTTP_200_OK
    assert second_response.status_code == status.HTTP_200_OK
    assert third_response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "Retry-After" in third_response


@pytest.mark.django_db
@patch.object(
    WriteRateThrottle,
    "rate",
    "2/min",
    create=True,
)
def test_write_throttle_returns_429() -> None:
    cache.clear()

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

    url = reverse("incidents:list-create")

    payload = {
        "organisation": str(organisation.pk),
        "title": "Suspicious authentication",
        "description": "Unexpected login activity.",
        "severity": Incident.Severity.HIGH,
    }

    first_response = client.post(
        url,
        payload,
        format="json",
    )

    second_response = client.post(
        url,
        payload,
        format="json",
    )

    third_response = client.post(
        url,
        payload,
        format="json",
    )

    assert first_response.status_code == status.HTTP_201_CREATED
    assert second_response.status_code == status.HTTP_201_CREATED
    assert third_response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
