"""
OpenTelemetry setup and initialization.
Handles distributed tracing and span creation across the entire system.
"""

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.propagators.jaeger_baggage import JaegerBaggagePropagator
from opentelemetry.propagators.b3 import B3Format
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.api.propagators.in_memory_text_propagator import InMemoryTextPropagator
import uuid

from src.core.config import settings


def init_tracing():
    """Initialize OpenTelemetry tracing with Jaeger exporter."""
    if not settings.JAEGER_ENABLED:
        print("[TRACING] Jaeger disabled, using no-op tracer")
        trace.set_tracer_provider(TracerProvider())
        return
    
    # Create resource with service metadata
    resource = Resource.create({
        "service.name": "url-shortener",
        "service.version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "deployment.environment": settings.ENVIRONMENT,
    })
    
    try:
        # Create Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=settings.JAEGER_HOST,
            agent_port=settings.JAEGER_PORT,
        )
        
        # Create tracer provider with resource
        tracer_provider = TracerProvider(resource=resource)
        
        # Add Jaeger exporter with batch processing
        tracer_provider.add_span_processor(
            BatchSpanProcessor(jaeger_exporter)
        )
        
        # Set global tracer provider
        trace.set_tracer_provider(tracer_provider)
        
        print(f"[TRACING] OpenTelemetry initialized with Jaeger at {settings.JAEGER_HOST}:{settings.JAEGER_PORT}")
    except Exception as e:
        print(f"[TRACING] Failed to initialize Jaeger exporter: {e}")
        trace.set_tracer_provider(TracerProvider(resource=resource))


def init_metrics():
    """Initialize OpenTelemetry metrics with Prometheus exporter."""
    if not settings.PROMETHEUS_ENABLED:
        print("[METRICS] Prometheus disabled, using no-op meter")
        metrics.set_meter_provider(MeterProvider())
        return
    
    try:
        # Create Prometheus exporter (will be scraped by prometheus)
        prometheus_reader = PrometheusMetricReader()
        
        # Create resource
        resource = Resource.create({
            "service.name": "url-shortener",
            "environment": settings.ENVIRONMENT,
        })
        
        # Create meter provider
        meter_provider = MeterProvider(
            metric_readers=[prometheus_reader],
            resource=resource,
        )
        
        # Set global meter provider
        metrics.set_meter_provider(meter_provider)
        
        print("[METRICS] OpenTelemetry Prometheus metrics initialized")
        return prometheus_reader
    except Exception as e:
        print(f"[METRICS] Failed to initialize Prometheus exporter: {e}")
        metrics.set_meter_provider(MeterProvider())
        return None


def instrument_fastapi(app):
    """Instrument FastAPI application with OpenTelemetry."""
    try:
        FastAPIInstrumentor.instrument_app(
            app,
            request_hook=None,
            response_hook=None,
            excluded_urls=["/health", "/metrics"],
        )
        print("[INSTRUMENTATION] FastAPI instrumented")
    except Exception as e:
        print(f"[INSTRUMENTATION] Failed to instrument FastAPI: {e}")


def instrument_sqlalchemy(engine):
    """Instrument SQLAlchemy with OpenTelemetry."""
    try:
        SQLAlchemyInstrumentor().instrument(
            engine=engine,
            service=settings.PROJECT_NAME,
        )
        print("[INSTRUMENTATION] SQLAlchemy instrumented")
    except Exception as e:
        print(f"[INSTRUMENTATION] Failed to instrument SQLAlchemy: {e}")


def instrument_redis(client):
    """Instrument Redis client with OpenTelemetry."""
    try:
        RedisInstrumentor().instrument(
            client=client,
            service=settings.PROJECT_NAME,
        )
        print("[INSTRUMENTATION] Redis instrumented")
    except Exception as e:
        print(f"[INSTRUMENTATION] Failed to instrument Redis: {e}")


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer instance for creating spans."""
    return trace.get_tracer(name, version="1.0.0")


def get_meter(name: str) -> metrics.Meter:
    """Get a meter instance for recording metrics."""
    return metrics.get_meter(name, version="1.0.0")


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracking."""
    return f"req-{uuid.uuid4().hex[:12]}"
