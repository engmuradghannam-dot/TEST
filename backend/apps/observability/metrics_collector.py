"""Metrics Collector: records business + technical metrics to DB and OTel."""
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    def record(self, name: str, value: float, company=None, **labels):
        from .models import Metric
        Metric.objects.create(company=company, name=name, value=value, labels=labels)
        try:
            from opentelemetry import metrics as otel_metrics
            meter = otel_metrics.get_meter("nexus")
            meter.create_gauge(name).set(value, attributes=labels)
        except Exception:
            pass

    def increment(self, name: str, company=None, by: float = 1.0, **labels):
        self.record(name, by, company=company, kind="counter", **labels)

    def query(self, name: str, company=None, since=None):
        from .models import Metric
        qs = Metric.objects.filter(name=name)
        if company is not None:
            qs = qs.filter(company=company)
        if since is not None:
            qs = qs.filter(recorded_at__gte=since)
        return qs.order_by('recorded_at')


collector = MetricsCollector()
