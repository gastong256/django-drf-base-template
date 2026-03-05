"""
Optional OpenTelemetry setup. Enabled via OTEL_ENABLED=true env var.
Install optional deps: uv sync --extra otel
"""

import os


def _float_env(name: str, default: float) -> float:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except ValueError:
        return default


def _bool_env(name: str, default: bool) -> bool:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return raw_value.lower() == "true"


def setup_otel() -> None:
    if not _bool_env("OTEL_ENABLED", False):
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.django import DjangoInstrumentor
        from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
        from opentelemetry.sdk.resources import DEPLOYMENT_ENVIRONMENT, SERVICE_NAME, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
    except ImportError as exc:
        raise ImportError(
            "OpenTelemetry packages not installed. Run: uv sync --extra otel"
        ) from exc

    service_name = os.environ.get("OTEL_SERVICE_NAME", "__SERVICE_NAME__")
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    deployment_environment = os.environ.get("APP_ENV", "local")
    sample_rate = _float_env("OTEL_TRACES_SAMPLER_ARG", 1.0)
    exporter_insecure = _bool_env("OTEL_EXPORTER_OTLP_INSECURE", True)

    resource = Resource.create(
        {
            SERVICE_NAME: service_name,
            DEPLOYMENT_ENVIRONMENT: deployment_environment,
        }
    )
    provider = TracerProvider(
        resource=resource,
        sampler=TraceIdRatioBased(sample_rate),
    )
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=exporter_insecure)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    DjangoInstrumentor().instrument()
    PsycopgInstrumentor().instrument()
