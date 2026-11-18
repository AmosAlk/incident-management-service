import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.celery import (
    CeleryInstrumentor,
)
from opentelemetry.instrumentation.django import (
    DjangoInstrumentor,
)
from opentelemetry.instrumentation.psycopg import (
    PsycopgInstrumentor,
)
from opentelemetry.sdk.resources import (
    SERVICE_NAME,
    Resource,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_configured = False


def configure_tracing(*, instrument_django: bool = True) -> None:
    global _configured

    if _configured:
        return

    if os.environ.get(
        "OTEL_TRACING_ENABLED",
        "false",
    ).lower() not in {
        "1",
        "true",
        "yes",
        "on",
    }:
        return

    # Creates metadata describing the service.
    # This gets attached to the spans.
    resource = Resource.create(
        {
            SERVICE_NAME: "incident-management-service",
        }
    )

    # Creates the SDK tracing provider and attaches the resource.
    provider = TracerProvider(resource=resource)

    otlp_endpoint = os.environ.get(
        "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
        "http://127.0.0.1:4318/v1/traces",
    )

    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=otlp_endpoint,
            )
        )
    )

    trace.set_tracer_provider(provider)

    if instrument_django:
        DjangoInstrumentor().instrument()

    PsycopgInstrumentor().instrument()

    CeleryInstrumentor().instrument()

    _configured = True
