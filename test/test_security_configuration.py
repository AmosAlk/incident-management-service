import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
@override_settings(
    SECURE_SSL_REDIRECT=True,
)
def test_http_request_redirects_when_ssl_redirect_enabled() -> None:
    client = APIClient()

    response = client.get(
        reverse("health-check"),
    )

    assert response.status_code == 301
    assert response["Location"].startswith("https://")
