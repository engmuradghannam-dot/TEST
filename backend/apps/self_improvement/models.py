from django.db import models


class ImprovementSuggestion(models.Model):
    STATUS = [('proposed', 'Proposed'), ('approved', 'Approved'),
              ('rejected', 'Rejected'), ('deployed', 'Deployed'),
              ('rolled_back', 'Rolled Back')]
    AREA = [('performance', 'Performance'), ('reliability', 'Reliability'),
            ('workflow', 'Workflow'), ('config', 'Configuration')]

    area = models.CharField(max_length=20, choices=AREA)
    title = models.CharField(max_length=200)
    analysis = models.TextField()
    proposed_change = models.JSONField(help_text="Structured change spec")
    confidence = models.FloatField(default=0.0)
    status = models.CharField(max_length=15, choices=STATUS, default='proposed')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey('accounts.User', null=True, blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name='approved_suggestions')
    deployed_at = models.DateTimeField(null=True, blank=True)
    rollback_snapshot = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"[{self.status}] {self.title}"
