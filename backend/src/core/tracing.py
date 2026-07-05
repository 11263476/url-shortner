"""OpenTelemetry setup and initialization."""

import uuid

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from src.core.config import settings


def init_tracing():
    """Initialize OpenTelemetry tracing with OTLP exporter to Grafana Cloud Tempo."""
    if not settings.PROMETHEUS_ENABLED:
        print("[TRACING] Tracing disabled, using no-op tracer")
        trace.set_tracer_provider(TracerProvider())
        return

    resource = Resource.create({
        "service.name": "url-shortener",
        "service.version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "deployment.environment": settings.ENVIRONMENT,
    })

    try:
        headers = {}
        if settings.OTEL_EXPORTER_OTLP_HEADERS:
            # Parse headers string "Authorization=Basic xxx" into dict
            for pair in settings.OTEL_EXPORTER_OTLP_HEADERS.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    headers[k.strip()] = v.strip()

        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
            headers=headers,
            timeout=5,
        )
        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        trace.set_tracer_provider(tracer_provider)
        print(f"[TRACING] OpenTelemetry initialized with OTLP at {settings.OTEL_EXPORTER_OTLP_ENDPOINT}")
    except Exception as e:
        print(f"[TRACING] Failed to initialize OTLP exporter: {e}")
        trace.set_tracer_provider(TracerProvider(resource=resource))


def init_metrics():
    """Initialize OpenTelemetry metrics with Prometheus exporter."""
    if not settings.PROMETHEUS_ENABLED:
        print("[METRICS] Prometheus disabled, using no-op meter")
        metrics.set_meter_provider(MeterProvider())
        return

    try:
        prometheus_reader = PrometheusMetricReader()
        resource = Resource.create({
            "service.name": "url-shortener",
            "environment": settings.ENVIRONMENT,
        })
        meter_provider = MeterProvider(metric_readers=[prometheus_reader], resource=resource)
        metrics.set_meter_provider(meter_provider)
        print("[METRICS] OpenTelemetry Prometheus metrics initialized")
        return prometheus_reader
    except Exception as e:
        print(f"[METRICS] Failed to initialize Prometheus exporter: {e}")
        metrics.set_meter_provider(MeterProvider())
        return None


def instrument_fastapi(app):
    try:
        FastAPIInstrumentor.instrument_app(app, excluded_urls="/health|/metrics")
        print("[INSTRUMENTATION] FastAPI instrumented")
    except Exception as e:
        print(f"[INSTRUMENTATION] Failed to instrument FastAPI: {e}")


def instrument_sqlalchemy(engine):
    try:
        SQLAlchemyInstrumentor().instrument(engine=engine, service=settings.PROJECT_NAME)
        print("[INSTRUMENTATION] SQLAlchemy instrumented")
    except Exception as e:
        print(f"[INSTRUMENTATION] Failed to instrument SQLAlchemy: {e}")


def instrument_redis(client):
    try:
        RedisInstrumentor().instrument(client=client, service=settings.PROJECT_NAME)
        print("[INSTRUMENTATION] Redis instrumented")
    except Exception as e:
        print(f"[INSTRUMENTATION] Failed to instrument Redis: {e}")


def get_tracer(name: str) -> trace.Tracer:
    return trace.get_tracer(name, version="1.0.0")


def get_meter(name: str) -> metrics.Meter:
    return metrics.get_meter(name, version="1.0.0")


def generate_correlation_id() -> str:
    return f"req-{uuid.uuid4().hex[:12]}"
