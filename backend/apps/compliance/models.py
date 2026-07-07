"""Compliance Automation: control catalog + evidence + continuous checks
for SOC 2 / ISO 27001 / ISO 9001 / GDPR."""
from django.db import models
from django.utils import timezone


class ComplianceFramework(models.Model):
    code = models.CharField(max_length=30, unique=True)   # soc2, iso27001...
    name = models.CharField(max_length=120)
    version = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.code


class ComplianceControl(models.Model):
    framework = models.ForeignKey(ComplianceFramework, on_delete=models.CASCADE,
                                  related_name='controls')
    control_id = models.CharField(max_length=40)          # e.g. CC6.1, A.9.2.1
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    automated_check = models.CharField(
        max_length=100, blank=True,
        help_text='dotted path to a callable(company)->bool for auto-evidence')

    class Meta:
        unique_together = [('framework', 'control_id')]

    def __str__(self):
        return f"{self.framework.code}:{self.control_id}"


class ControlAssessment(models.Model):
    STATUS = [('pass', 'Pass'), ('fail', 'Fail'),
              ('partial', 'Partial'), ('not_assessed', 'Not Assessed')]
    control = models.ForeignKey(ComplianceControl, on_delete=models.CASCADE,
                                related_name='assessments')
    status = models.CharField(max_length=15, choices=STATUS,
                              default='not_assessed')
    evidence = models.JSONField(default=dict, blank=True)
    assessed_at = models.DateTimeField(default=timezone.now)
    automated = models.BooleanField(default=False)
