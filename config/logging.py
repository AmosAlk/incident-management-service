import json
import logging
from datetime import UTC, datetime
from typing import Any

from config.request_context import get_request_id

STRUCTURED_FIELDS = (
    "request_id",
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
