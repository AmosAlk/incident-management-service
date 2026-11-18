import logging
from uuid import UUID

import pytest
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory

from config.middleware import RequestIDMiddleware
from config.request_context import get_request_id


def successful_response(
    _request: HttpRequest,
) -> HttpResponse:
    return HttpResponse(status=204)


def test_request_id_is_generated() -> None:
    request = RequestFactory().get("/test/")

    middleware = RequestIDMiddleware(successful_response)

    response = middleware(request)

    request_id = response["X-Request-ID"]

    UUID(request_id)


def test_client_supplied_request_id_is_ignored() -> None:
    supplied_request_id = "11111111-1111-1111-1111-111111111111"

    request = RequestFactory().get(
        "/test/",
        HTTP_X_REQUEST_ID=supplied_request_id,
    )

    middleware = RequestIDMiddleware(successful_response)

    response = middleware(request)

    generated_request_id = response["X-Request-ID"]

    assert generated_request_id != supplied_request_id

    UUID(generated_request_id)


def test_request_context_is_available_during_request() -> None:
    observed_request_id: str | None = None

    def response_with_context(
        request: HttpRequest,
    ) -> HttpResponse:
        nonlocal observed_request_id

        observed_request_id = get_request_id()

        assert observed_request_id == request.request_id

        return HttpResponse(status=204)

    request = RequestFactory().get("/test/")

    middleware = RequestIDMiddleware(response_with_context)

    middleware(request)

    assert observed_request_id is not None


def test_request_context_is_cleared_after_request() -> None:
    assert get_request_id() is None

    request = RequestFactory().get("/test/")

    middleware = RequestIDMiddleware(successful_response)

    middleware(request)

    assert get_request_id() is None


def test_completed_request_is_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    request = RequestFactory().post("/api/incidents/")

    middleware = RequestIDMiddleware(successful_response)

    with caplog.at_level(
        logging.INFO,
        logger="api.request",
    ):
        response = middleware(request)

    record = next(
        record
        for record in caplog.records
        if record.getMessage() == "request_completed"
    )

    assert record.method == "POST"
    assert record.path == "/api/incidents/"
    assert record.status_code == 204
    assert record.duration_ms >= 0
    assert record.request_id == response["X-Request-ID"]
