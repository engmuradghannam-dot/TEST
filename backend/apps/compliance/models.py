from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class ComplianceFramework(models.Model):
    """Global compliance frameworks (ISO, HIPAA, Basel, etc.)"""
    framework_id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=100, choices=[
        ('financial', 'Financial'), ('healthcare', 'Healthcare'), ('manufacturing', 'Manufacturing'),
        ('it_security', 'IT Security'), ('environmental', 'Environmental'), ('general', 'General')
    ])
    description = models.TextField()
    version = models.CharField(max_length=50, blank=True)
    issuing_body = models.CharField(max_length=255, blank=True)
    effective_date = models.DateField(null=True, blank=True)
    review_cycle_months = models.PositiveIntegerField(default=12)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Compliance Framework'

    def __str__(self):
        return f"{self.framework_id} - {self.name}"


class ComplianceRequirement(models.Model):
    """Specific requirements within a framework"""
    SEVERITY_CHOICES = [
        ('critical', 'Critical'), ('high', 'High'), ('medium', 'Medium'), ('low', 'Low')
    ]
    framework = models.ForeignKey(ComplianceFramework, on_delete=models.CASCADE, related_name='requirements')
    requirement_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    verification_method = models.TextField(blank=True)
    documentation_required = models.BooleanField(default=True)
    review_frequency_days = models.PositiveIntegerField(default=90)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['framework', 'requirement_id']
        ordering = ['framework', 'requirement_id']

    def __str__(self):
        return f"{self.requirement_id}: {self.title}"


class CompanyCompliance(models.Model):
    """Company compliance status per framework"""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'), ('in_progress', 'In Progress'),
        ('compliant', 'Compliant'), ('non_compliant', 'Non-Compliant'),
        ('exempt', 'Exempt'), ('under_review', 'Under Review')
    ]
    from apps.core.models import Company

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='compliance_records')
    framework = models.ForeignKey(ComplianceFramework, on_delete=models.CASCADE, related_name='company_records')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    compliance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    last_assessment_date = models.DateField(null=True, blank=True)
    next_assessment_date = models.DateField(null=True, blank=True)
    assessor = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)
    findings = models.TextField(blank=True)
    action_plan = models.TextField(blank=True)
    documents = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['company', 'framework']
        verbose_name = 'Company Compliance'
        verbose_name_plural = 'Company Compliance Records'

    def __str__(self):
        return f"{self.company.name} - {self.framework.name}"


class ComplianceAudit(models.Model):
    """Individual compliance audit records"""
    RESULT_CHOICES = [
        ('pass', 'Pass'), ('fail', 'Fail'), ('partial', 'Partial'), ('na', 'N/A')
    ]
    company_compliance = models.ForeignKey(CompanyCompliance, on_delete=models.CASCADE, related_name='audits')
    requirement = models.ForeignKey(ComplianceRequirement, on_delete=models.CASCADE, related_name='audits')
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='na')
    evidence = models.TextField(blank=True)
    evidence_files = models.JSONField(default=list, blank=True)
    auditor = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)
    audit_date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)
    remediation_required = models.BooleanField(default=False)
    remediation_deadline = models.DateField(null=True, blank=True)
    remediation_status = models.CharField(max_length=20, default='none', choices=[
        ('none', 'None'), ('planned', 'Planned'), ('in_progress', 'In Progress'), ('completed', 'Completed')
    ])

    class Meta:
        ordering = ['-audit_date']

    def __str__(self):
        return f"{self.requirement.requirement_id} - {self.result}"


class RegulatoryUpdate(models.Model):
    """Track regulatory changes and updates"""
    framework = models.ForeignKey(ComplianceFramework, on_delete=models.CASCADE, related_name='updates')
    title = models.CharField(max_length=255)
    description = models.TextField()
    effective_date = models.DateField()
    impact_level = models.CharField(max_length=20, default='medium', choices=[
        ('critical', 'Critical'), ('high', 'High'), ('medium', 'Medium'), ('low', 'Low')
    ])
    action_required = models.BooleanField(default=False)
    action_description = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
