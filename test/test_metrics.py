import pytest
from django.test import Client
from prometheus_client import REGISTRY


def metric_value(
    name: str,
    labels: dict[str, str] | None = None,
) -> float:
    value = REGISTRY.get_sample_value(
        name,
        labels or {},
    )

    return 0.0 if value is None else value


@pytest.mark.django_db
def test_metrics_endpoint_exposes_prometheus_metrics() -> None:
    client = Client()

    response = client.get("/metrics/")

    assert response.status_code == 200

    body = response.content.decode()

    assert "incident_service_http_requests_total" in body
    assert "incident_service_http_request_duration_seconds" in body
    assert "incident_service_incidents_created_total" in body


@pytest.mark.django_db
def test_http_request_counter_increments() -> None:
    client = Client()

    labels = {
        "method": "GET",
        "status": "200",
    }

    before = metric_value(
        "incident_service_http_requests_total",
        labels,
    )

    response = client.get("/api/health/")

    assert response.status_code == 200

    after = metric_value(
        "incident_service_http_requests_total",
        labels,
    )

    assert after == before + 1


@pytest.mark.django_db
def test_http_duration_histogram_observes_request() -> None:
    client = Client()

    labels = {
        "method": "GET",
        "status": "200",
    }

    before = metric_value(
        "incident_service_http_request_duration_seconds_count",
        labels,
    )

    response = client.get("/api/health/")

    assert response.status_code == 200

    after = metric_value(
        "incident_service_http_request_duration_seconds_count",
        labels,
    )

    assert after == before + 1
