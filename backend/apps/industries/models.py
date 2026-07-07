from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import json

class IndustryCatalog(models.Model):
    """Master catalog of 100+ supported industries"""
    industry_id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    description_ar = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True, default='Building2')
    color = models.CharField(max_length=20, default='#3b82f6')
    is_active = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False)
    required_license_tier = models.CharField(max_length=50, default='starter', choices=[
        ('starter', 'Starter'), ('business', 'Business'), ('industry', 'Industry'), ('enterprise', 'Enterprise AI')
    ])
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'Industry Catalog'
        verbose_name_plural = 'Industry Catalogs'

    def __str__(self):
        return f"{self.industry_id} - {self.name}"


class IndustryControl(models.Model):
    """Industry-specific controls (80+ controls per industry)"""
    CONTROL_TYPES = [
        ('operational', 'Operational'),
        ('financial', 'Financial'),
        ('compliance', 'Compliance'),
        ('safety', 'Safety'),
        ('quality', 'Quality'),
        ('environmental', 'Environmental'),
        ('security', 'Security'),
        ('hr', 'Human Resources'),
    ]

    SEVERITY_LEVELS = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    industry = models.ForeignKey(IndustryCatalog, on_delete=models.CASCADE, related_name='controls')
    control_id = models.CharField(max_length=50, db_index=True)
    module = models.CharField(max_length=100)
    control_name = models.CharField(max_length=255)
    control_name_ar = models.CharField(max_length=255, blank=True)
    sub_control = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    description_ar = models.TextField(blank=True)
    control_type = models.CharField(max_length=20, choices=CONTROL_TYPES, default='operational')
    is_required = models.BooleanField(default=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='medium')
    ai_agent_name = models.CharField(max_length=100, blank=True)
    ai_agent_description = models.TextField(blank=True)
    database_entity = models.CharField(max_length=100, blank=True)
    kpi_name = models.CharField(max_length=100, blank=True)
    kpi_formula = models.CharField(max_length=255, blank=True)
    kpi_target = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    kpi_unit = models.CharField(max_length=50, blank=True)
    compliance_framework = models.CharField(max_length=100, blank=True)
    compliance_standard = models.CharField(max_length=100, blank=True)
    regulatory_reference = models.CharField(max_length=255, blank=True)
    implementation_guide = models.TextField(blank=True)
    implementation_guide_ar = models.TextField(blank=True)
    automation_rules = models.JSONField(default=dict, blank=True)
    checklists = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['industry', 'sort_order', 'control_id']
        unique_together = ['industry', 'control_id']
        verbose_name = 'Industry Control'
        verbose_name_plural = 'Industry Controls'

    def __str__(self):
        return f"{self.control_id} - {self.control_name}"


class AIAgentRegistry(models.Model):
    """Registry of AI agents per industry"""
    AGENT_TYPES = [
        ('predictive', 'Predictive'),
        ('analytical', 'Analytical'),
        ('automation', 'Automation'),
        ('advisory', 'Advisory'),
        ('monitoring', 'Monitoring'),
    ]

    industry = models.ForeignKey(IndustryCatalog, on_delete=models.CASCADE, related_name='ai_agents')
    agent_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    agent_type = models.CharField(max_length=20, choices=AGENT_TYPES, default='analytical')
    description = models.TextField()
    description_ar = models.TextField(blank=True)
    responsibilities = models.JSONField(default=list)
    database_entities = models.JSONField(default=list)
    model_config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    usage_count = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['industry', 'name']
        verbose_name = 'AI Agent'
        verbose_name_plural = 'AI Agents'

    def __str__(self):
        return f"{self.agent_id} - {self.name}"


class CompanyIndustryProfile(models.Model):
    """Links a company to its selected industries and active controls"""
    from apps.core.models import Company

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='industry_profiles')
    industry = models.ForeignKey(IndustryCatalog, on_delete=models.CASCADE, related_name='company_profiles')
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    deployment_date = models.DateField(null=True, blank=True)
    activated_controls = models.ManyToManyField(IndustryControl, blank=True, related_name='company_profiles')
    activated_agents = models.ManyToManyField(AIAgentRegistry, blank=True, related_name='company_profiles')
    custom_settings = models.JSONField(default=dict, blank=True)
    compliance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    maturity_level = models.CharField(max_length=20, default='initial', choices=[
        ('initial', 'Initial'), ('developing', 'Developing'), ('defined', 'Defined'),
        ('managed', 'Managed'), ('optimizing', 'Optimizing')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['company', 'industry']
        verbose_name = 'Company Industry Profile'
        verbose_name_plural = 'Company Industry Profiles'

    def __str__(self):
        return f"{self.company.name} - {self.industry.name}"


class ControlExecutionLog(models.Model):
    """Audit log of control executions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('warning', 'Warning'),
        ('skipped', 'Skipped'),
    ]

    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='control_logs')
    control = models.ForeignKey(IndustryControl, on_delete=models.CASCADE, related_name='execution_logs')
    executed_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    result_data = models.JSONField(default=dict, blank=True)
    findings = models.TextField(blank=True)
    risk_level = models.CharField(max_length=20, blank=True)
    remediation_notes = models.TextField(blank=True)
    executed_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-executed_at']
        verbose_name = 'Control Execution Log'
        verbose_name_plural = 'Control Execution Logs'

    def __str__(self):
        return f"{self.control.control_id} - {self.status}"
