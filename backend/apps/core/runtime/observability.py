"""
Observability Layer for Nexus CE-ERP OS
Features: Azure Monitor, OpenTelemetry, Distributed Tracing, Business Metrics, Alerts
"""
import os
import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from functools import wraps
from django.conf import settings

logger = logging.getLogger(__name__)

# ============================================================
# OpenTelemetry Setup
# ============================================================

def setup_telemetry():
    """Initialize OpenTelemetry with Azure Monitor"""
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.django import DjangoInstrumentor
        from opentelemetry.instrumentation.celery import CeleryInstrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        # Set up tracer provider
        provider = TracerProvider()
        trace.set_tracer_provider(provider)

        # OTLP exporter (for Azure Monitor or other backends)
        otlp_endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4317')
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)

        # Add span processor
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        # Instrument Django
        DjangoInstrumentor().instrument()

        # Instrument Celery
        CeleryInstrumentor().instrument()

        # Instrument Redis
        RedisInstrumentor().instrument()

        logger.info("OpenTelemetry initialized")
        return provider
    except Exception as e:
        logger.warning(f"OpenTelemetry initialization failed: {e}")
        return None


# ============================================================
# Metrics Collector
# ============================================================

class MetricsCollector:
    """Collects and exposes business and system metrics"""

    def __init__(self):
        self._metrics = {}
        self._counters = {}
        self._gauges = {}
        self._histograms = {}

    def counter(self, name: str, value: float = 1, tags: Dict = None):
        """Increment a counter metric"""
        key = self._make_key(name, tags)
        self._counters[key] = self._counters.get(key, 0) + value

    def gauge(self, name: str, value: float, tags: Dict = None):
        """Set a gauge metric"""
        key = self._make_key(name, tags)
        self._gauges[key] = value

    def histogram(self, name: str, value: float, tags: Dict = None):
        """Record a histogram value"""
        key = self._make_key(name, tags)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)

    def _make_key(self, name: str, tags: Dict = None) -> str:
        if not tags:
            return name
        tag_str = ','.join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{tag_str}}}"

    def get_metrics(self) -> Dict:
        """Get all metrics in Prometheus format"""
        lines = []

        # Counters
        for key, value in self._counters.items():
            lines.append(f"# TYPE {key.split('{')[0]} counter")
            lines.append(f"{key} {value}")

        # Gauges
        for key, value in self._gauges.items():
            lines.append(f"# TYPE {key.split('{')[0]} gauge")
            lines.append(f"{key} {value}")

        # Histograms
        for key, values in self._histograms.items():
            if values:
                lines.append(f"# TYPE {key.split('{')[0]} histogram")
                lines.append(f"{key}_count {len(values)}")
                lines.append(f"{key}_sum {sum(values)}")
                lines.append(f"{key}_avg {sum(values)/len(values)}")

        return '\n'.join(lines)

    def get_business_metrics(self) -> Dict:
        """Get business-specific metrics"""
        return {
            'counters': self._counters,
            'gauges': self._gauges,
            'histograms': {k: {'count': len(v), 'sum': sum(v), 'avg': sum(v)/len(v)} 
                          for k, v in self._histograms.items()}
        }


metrics_collector = MetricsCollector()


# ============================================================
# Business Metrics
# ============================================================

class BusinessMetrics:
    """Business-specific metrics collection"""

    @staticmethod
    def record_invoice_created(amount: float, tenant_id: str):
        metrics_collector.counter('business.invoices.created', 1, {'tenant': tenant_id})
        metrics_collector.histogram('business.invoices.amount', amount, {'tenant': tenant_id})

    @staticmethod
    def record_invoice_paid(amount: float, days_to_pay: int, tenant_id: str):
        metrics_collector.counter('business.invoices.paid', 1, {'tenant': tenant_id})
        metrics_collector.histogram('business.invoices.days_to_pay', days_to_pay, {'tenant': tenant_id})

    @staticmethod
    def record_purchase_order_created(amount: float, tenant_id: str):
        metrics_collector.counter('business.purchase_orders.created', 1, {'tenant': tenant_id})
        metrics_collector.histogram('business.purchase_orders.amount', amount, {'tenant': tenant_id})

    @staticmethod
    def record_sales_order_created(amount: float, tenant_id: str):
        metrics_collector.counter('business.sales_orders.created', 1, {'tenant': tenant_id})
        metrics_collector.histogram('business.sales_orders.amount', amount, {'tenant': tenant_id})

    @staticmethod
    def record_employee_hired(tenant_id: str):
        metrics_collector.counter('business.employees.hired', 1, {'tenant': tenant_id})

    @staticmethod
    def record_workflow_completed(duration_seconds: float, tenant_id: str):
        metrics_collector.counter('business.workflows.completed', 1, {'tenant': tenant_id})
        metrics_collector.histogram('business.workflows.duration', duration_seconds, {'tenant': tenant_id})

    @staticmethod
    def record_ai_prediction(model_type: str, confidence: float, tenant_id: str):
        metrics_collector.counter('business.ai.predictions', 1, {'model': model_type, 'tenant': tenant_id})
        metrics_collector.histogram('business.ai.confidence', confidence, {'model': model_type, 'tenant': tenant_id})

    @staticmethod
    def record_user_login(tenant_id: str):
        metrics_collector.counter('business.users.login', 1, {'tenant': tenant_id})

    @staticmethod
    def record_api_latency(endpoint: str, latency_ms: float, tenant_id: str):
        metrics_collector.histogram('system.api.latency', latency_ms, {'endpoint': endpoint, 'tenant': tenant_id})

    @staticmethod
    def record_error(module: str, error_type: str, tenant_id: str):
        metrics_collector.counter('system.errors', 1, {'module': module, 'type': error_type, 'tenant': tenant_id})


# ============================================================
# Alert System
# ============================================================

class AlertRule:
    """Defines an alert condition"""

    def __init__(self, name: str, metric: str, condition: str, threshold: float,
                 duration_minutes: int = 5, severity: str = 'warning'):
        self.name = name
        self.metric = metric
        self.condition = condition  # 'gt', 'lt', 'eq'
        self.threshold = threshold
        self.duration_minutes = duration_minutes
        self.severity = severity
        self._history = []

    def check(self, value: float) -> bool:
        """Check if alert should fire"""
        triggered = False
        if self.condition == 'gt':
            triggered = value > self.threshold
        elif self.condition == 'lt':
            triggered = value < self.threshold
        elif self.condition == 'eq':
            triggered = value == self.threshold

        now = datetime.now()
        self._history.append({'time': now, 'value': value, 'triggered': triggered})

        # Clean old history
        cutoff = now - timedelta(minutes=self.duration_minutes)
        self._history = [h for h in self._history if h['time'] > cutoff]

        # Check if consistently triggered
        if len(self._history) >= 3:
            recent = self._history[-3:]
            if all(h['triggered'] for h in recent):
                return True

        return False


class AlertManager:
    """Manages alert rules and notifications"""

    def __init__(self):
        self.rules: List[AlertRule] = []
        self._alerts_fired = {}

    def add_rule(self, rule: AlertRule):
        self.rules.append(rule)

    def check_all(self, metrics: Dict) -> List[Dict]:
        """Check all rules against current metrics"""
        alerts = []
        for rule in self.rules:
            value = metrics.get(rule.metric, 0)
            if rule.check(value):
                alert_key = f"{rule.name}:{rule.metric}"
                if alert_key not in self._alerts_fired:
                    self._alerts_fired[alert_key] = datetime.now()
                    alerts.append({
                        'rule': rule.name,
                        'metric': rule.metric,
                        'value': value,
                        'threshold': rule.threshold,
                        'severity': rule.severity,
                        'message': f"{rule.name}: {rule.metric} is {value} (threshold: {rule.threshold})"
                    })
        return alerts

    def clear_alert(self, alert_key: str):
        if alert_key in self._alerts_fired:
            del self._alerts_fired[alert_key]


# Predefined alert rules
alert_manager = AlertManager()
alert_manager.add_rule(AlertRule(
    name="High Error Rate",
    metric="system.errors",
    condition="gt",
    threshold=10,
    severity="critical"
))
alert_manager.add_rule(AlertRule(
    name="High API Latency",
    metric="system.api.latency",
    condition="gt",
    threshold=2000,  # 2 seconds
    severity="warning"
))
alert_manager.add_rule(AlertRule(
    name="SLA Violation",
    metric="business.workflows.duration",
    condition="gt",
    threshold=3600,  # 1 hour
    severity="critical"
))
alert_manager.add_rule(AlertRule(
    name="Low AI Confidence",
    metric="business.ai.confidence",
    condition="lt",
    threshold=0.5,
    severity="warning"
))


# ============================================================
# Tracing Decorator
# ============================================================

def trace_span(name: str = None, attributes: Dict = None):
    """Decorator to trace function execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            span_name = name or func.__name__
            try:
                from opentelemetry import trace
                tracer = trace.get_tracer(__name__)
                with tracer.start_as_current_span(span_name) as span:
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, value)
                    result = func(*args, **kwargs)
                    span.set_attribute('status', 'success')
                    return result
            except ImportError:
                return func(*args, **kwargs)
        return wrapper
    return decorator


def timed_metric(metric_name: str, tags: Dict = None):
    """Decorator to time function execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = (time.time() - start) * 1000  # ms
                metrics_collector.histogram(metric_name, duration, tags)
        return wrapper
    return decorator


# ============================================================
# Health Check
# ============================================================

class HealthCheck:
    """System health check"""

    @staticmethod
    def check_database() -> Dict:
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return {'status': 'healthy', 'latency_ms': 0}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    @staticmethod
    def check_redis() -> Dict:
        try:
            import redis
            r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
            r.ping()
            return {'status': 'healthy', 'latency_ms': 0}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    @staticmethod
    def check_celery() -> Dict:
        try:
            from celery import current_app
            inspect = current_app.control.inspect()
            active = inspect.active()
            return {'status': 'healthy', 'workers': len(active) if active else 0}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    @staticmethod
    def check_all() -> Dict:
        return {
            'database': HealthCheck.check_database(),
            'redis': HealthCheck.check_redis(),
            'celery': HealthCheck.check_celery(),
            'timestamp': datetime.now().isoformat()
        }
