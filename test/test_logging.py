import json
import logging

from config.logging import (
    JsonFormatter,
    RequestContextFilter,
)
from config.request_context import (
    reset_request_id,
    set_request_id,
)


def make_log_record(
    message: str,
) -> logging.LogRecord:
    return logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=None,
    )


def test_request_context_filter_adds_request_id() -> None:
    request_id = "f04200aa-d13e-4df8-88f6-9db62bcf29df"

    token = set_request_id(request_id)

    try:
        record = make_log_record("test_event")

        log_filter = RequestContextFilter()
        log_filter.filter(record)

        assert record.request_id == request_id

    finally:
        reset_request_id(token)


def test_json_formatter_creates_structured_log() -> None:
    record = make_log_record("request_completed")

    record.request_id = "f04200aa-d13e-4df8-88f6-9db62bcf29df"
    record.method = "POST"
    record.path = "/api/incidents/"
    record.status_code = 201
    record.duration_ms = 42.7

    formatter = JsonFormatter()

    formatted = formatter.format(record)

    payload = json.loads(formatted)

    assert payload["level"] == "INFO"
    assert payload["logger"] == "test.logger"
    assert payload["message"] == "request_completed"
    assert payload["method"] == "POST"
    assert payload["path"] == "/api/incidents/"
    assert payload["status_code"] == 201
    assert payload["duration_ms"] == 42.7
    assert payload["request_id"] == "f04200aa-d13e-4df8-88f6-9db62bcf29df"
    assert "timestamp" in payload


def test_json_formatter_does_not_include_arbitrary_fields() -> None:
    record = make_log_record("test_event")

    record.authorization = "Bearer super-secret-token"
    record.request_body = {"password": "super-secret-password"}

    formatter = JsonFormatter()

    formatted = formatter.format(record)

    payload = json.loads(formatted)

    assert "authorization" not in payload
    assert "request_body" not in payload
    assert "super-secret-token" not in formatted
    assert "super-secret-password" not in formatted
