"""Monitoring layer: samples system health signals into metrics."""
from datetime import timedelta

from django.utils import timezone

from apps.observability.metrics_collector import collector


def sample_health():
    """Run from Celery beat. Feeds the metrics the AI analyzer reads."""
    from apps.observability.models import Alert
    collector.record("alerts.open.count",
                     Alert.objects.filter(status="open").count())
    try:
        from apps.workflow.models import ApprovalRecord
        stale = ApprovalRecord.objects.filter(
            status="pending",
            created_at__lt=timezone.now() - timedelta(days=3)).count()
        collector.record("workflow.stuck.count", stale)
    except Exception:
        pass
    try:
        from django.db import connection
        collector.record("db.connection.queries", len(connection.queries))
    except Exception:
        pass
