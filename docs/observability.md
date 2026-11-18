# Observability

## Purpose

The service uses structured logging and correlation identifiers to make
production behaviour easier to inspect, debug, and investigate.

The current observability implementation focuses on logs and correlation.
Metrics and distributed tracing are planned as later layers.

## Structured Logging

Application logs are emitted as JSON.

Each log contains a core set of fields:

- `timestamp`
- `level`
- `logger`
- `message`

Additional structured fields are included when relevant, such as:

- `request_id`
- `method`
- `path`
- `status_code`
- `duration_ms`
- `task_id`
- `delivery_id`
- `incident_id`
- `delivery_status`
- `attempt`
- `recipient_count`
- `error_type`
- `retry_in_seconds`

Structured logs make it possible for log-processing systems to search,
filter, aggregate, and correlate events without parsing human-oriented
log strings.

## HTTP Request Correlation

Every HTTP request handled by Django receives a newly generated UUID.

The identifier is stored in request-local context and is available to
logging throughout the request lifecycle.

The identifier is also returned to the client through the response
header:

```text
X-Request-ID

## Metrics

The service exposes Prometheus-compatible application metrics.

The Django process exposes metrics through:

```text
GET /metrics/

## Distributed Tracing

The service uses OpenTelemetry for distributed tracing.

Tracing currently instruments:

- Django HTTP request handling
- PostgreSQL operations through Psycopg
- Celery task publication and execution

Trace data is exported using OTLP/HTTP to Jaeger during local
development.

The local Jaeger UI is available at: 

```text
http://localhost:16686