import json
import logging
from datetime import UTC, datetime
from typing import Any

from opentelemetry import trace

from config.request_context import get_request_id

STRUCTURED_FIELDS = (
    "request_id",
    "trace_id",
    "span_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "task_id",
    "delivery_id",
    "incident_id",
    "delivery_status",
    "attempt",
    "recipient_count",
    "error_type",
    "retry_in_seconds",
)


class RequestContextFilter(logging.Filter):
    def filter(
        self,
        record: logging.LogRecord,
    ) -> bool:
        if getattr(record, "request_id", None) is None:
            record.request_id = get_request_id()

        current_span = trace.get_current_span()
        span_context = current_span.get_span_context()

        if span_context.is_valid:
            if getattr(record, "trace_id", None) is None:
                record.trace_id = f"{span_context.trace_id:032x}"

            if getattr(record, "span_id", None) is None:
                record.span_id = f"{span_context.span_id:016x}"

        return True


class JsonFormatter(logging.Formatter):
    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
        timestamp = (
            datetime.fromtimestamp(
                record.created,
                tz=UTC,
            )
            .isoformat(timespec="milliseconds")
            .replace(
                "+00:00",
                "Z",
            )
        )

        payload: dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # For each possible Json field, get attribute of current
        # logging record, and set payload[field] to that value if
        # it exists.
        for field in STRUCTURED_FIELDS:
            value = getattr(
                record,
                field,
                None,
            )

            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )
