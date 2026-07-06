"""Alert Manager: SLA / Error / Workflow / Business alert rules.

evaluate_rules() is intended to run from Celery beat every minute.
Fires Alert rows + event-bus notifications; auto-resolves when clear.
"""
import logging
from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)

DEFAULT_RULES = [
    {"name": "api_error_rate", "category": "error", "metric": "http.5xx.count",
     "window_min": 5, "threshold": 10, "severity": "critical",
     "title": "High API error rate"},
    {"name": "workflow_stuck", "category": "workflow", "metric": "workflow.stuck.count",
     "window_min": 30, "threshold": 1, "severity": "warning",
     "title": "Workflow instances stuck"},
    {"name": "sla_response", "category": "sla", "metric": "http.p95.latency_ms",
     "window_min": 5, "threshold": 2000, "severity": "warning",
     "title": "p95 latency SLA breach", "agg": "avg"},
    {"name": "negative_stock", "category": "business", "metric": "inventory.negative.count",
     "window_min": 60, "threshold": 1, "severity": "critical",
     "title": "Negative stock detected"},
]


class AlertManager:
    def __init__(self, rules=None):
        self.rules = rules or DEFAULT_RULES

    def evaluate_rules(self):
        from django.db.models import Sum, Avg
        from .models import Metric, Alert
        from apps.core.event_bus import bus

        now = timezone.now()
        for rule in self.rules:
            since = now - timedelta(minutes=rule["window_min"])
            qs = Metric.objects.filter(name=rule["metric"], recorded_at__gte=since)
            agg = qs.aggregate(v=Avg("value") if rule.get("agg") == "avg" else Sum("value"))
            value = agg["v"] or 0
            breached = value >= rule["threshold"]

            open_alert = Alert.objects.filter(
                title=rule["title"], status="open").first()
            if breached and not open_alert:
                alert = Alert.objects.create(
                    category=rule["category"], severity=rule["severity"],
                    title=rule["title"],
                    detail=f"{rule['metric']}={value} over {rule['window_min']}m "
                           f"(threshold {rule['threshold']})",
                )
                bus.emit("alert.fired", {"alert_id": alert.pk, "title": alert.title,
                                         "severity": alert.severity})
                logger.error("ALERT FIRED: %s (%s)", alert.title, alert.detail)
            elif not breached and open_alert:
                open_alert.status = "resolved"
                open_alert.resolved_at = now
                open_alert.save(update_fields=["status", "resolved_at"])
                bus.emit("alert.resolved", {"alert_id": open_alert.pk})


manager = AlertManager()
