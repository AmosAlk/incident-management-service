from prometheus_client import Counter, Histogram

HTTP_REQUESTS_TOTAL = Counter(
    "incident_service_http_requests_total",
    "Total number of HTTP requests handled by Django.",
    [
        "method",
        "status",
    ],
)


HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "incident_service_http_request_duration_seconds",
    "Time spent handling HTTP requests.",
    [
        "method",
        "status",
    ],
    buckets=(
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
    ),
)


INCIDENTS_CREATED_TOTAL = Counter(
    "incident_service_incidents_created_total",
    "Total number of incidents successfully created.",
)

# result can be sent, skipped etc.
NOTIFICATION_DELIVERIES_TOTAL = Counter(
    "incident_service_notification_deliveries_total",
    "Total number of completed incident notification deliveries.",
    [
        "result",
    ],
)


NOTIFICATION_RETRIES_TOTAL = Counter(
    "incident_service_notification_retries_total",
    "Total number of incident notification retries requested.",
)
