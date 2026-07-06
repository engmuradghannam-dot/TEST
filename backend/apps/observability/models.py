from django.db import models


class Metric(models.Model):
    """Time-series business/technical metric point."""
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE,
                                null=True, blank=True, related_name='metrics')
    name = models.CharField(max_length=120, db_index=True)
    value = models.FloatField()
    labels = models.JSONField(default=dict, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=['name', 'recorded_at'])]

    def __str__(self):
        return f"{self.name}={self.value}"


class Alert(models.Model):
    SEVERITY = [('info', 'Info'), ('warning', 'Warning'), ('critical', 'Critical')]
    CATEGORY = [('sla', 'SLA'), ('error', 'Error'),
                ('workflow', 'Workflow'), ('business', 'Business')]
    STATUS = [('open', 'Open'), ('acknowledged', 'Acknowledged'), ('resolved', 'Resolved')]

    company = models.ForeignKey('core.Company', on_delete=models.CASCADE,
                                null=True, blank=True, related_name='alerts')
    category = models.CharField(max_length=20, choices=CATEGORY)
    severity = models.CharField(max_length=10, choices=SEVERITY, default='warning')
    title = models.CharField(max_length=200)
    detail = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=STATUS, default='open')
    fired_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"[{self.severity}] {self.title}"
