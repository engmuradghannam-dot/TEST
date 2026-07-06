"""OpenTelemetry bootstrap: traces + metrics exported over OTLP.

Call setup_telemetry() once from wsgi/asgi/celery startup. No-ops
cleanly when the opentelemetry packages are not installed.
"""
import logging
import os

logger = logging.getLogger(__name__)

_initialized = False


def setup_telemetry(service_name: str = "nexus-backend"):
    global _initialized
    if _initialized:
        return
    try:
        from opentelemetry import trace, metrics
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
        from opentelemetry.instrumentation.django import DjangoInstrumentor
    except ImportError:
        logger.warning("opentelemetry not installed - telemetry disabled")
        return

    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    resource = Resource.create({"service.name": service_name})

    tp = TracerProvider(resource=resource)
    tp.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(tp)

    reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=endpoint))
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))

    DjangoInstrumentor().instrument()
    _initialized = True
    logger.info("telemetry initialized -> %s", endpoint)


def get_tracer(name: str = "nexus"):
    try:
        from opentelemetry import trace
        return trace.get_tracer(name)
    except ImportError:
        import contextlib

        class _Noop:
            @contextlib.contextmanager
            def start_as_current_span(self, *_a, **_k):
                yield None
        return _Noop()
