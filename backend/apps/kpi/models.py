from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class KPIDefinition(models.Model):
    CATEGORIES = [
        ('financial', 'Financial'), ('operational', 'Operational'),
        ('quality', 'Quality'), ('safety', 'Safety'), ('customer', 'Customer'),
        ('employee', 'Employee'), ('environmental', 'Environmental')
    ]
    FREQUENCIES = [
        ('realtime', 'Real-time'), ('hourly', 'Hourly'), ('daily', 'Daily'),
        ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')
    ]
    kpi_id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORIES, default='operational')
    description = models.TextField()
    formula = models.CharField(max_length=500, blank=True)
    unit = models.CharField(max_length=50, blank=True)
    target_value = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    min_acceptable = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    max_acceptable = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCIES, default='monthly')
    data_source = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'KPI Definition'

    def __str__(self):
        return f"{self.kpi_id} - {self.name}"

class CompanyKPI(models.Model):
    from apps.core.models import Company
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='kpis')
    kpi = models.ForeignKey(KPIDefinition, on_delete=models.CASCADE, related_name='company_records')
    current_value = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    previous_value = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    trend = models.CharField(max_length=20, default='neutral', choices=[
        ('up', 'Up'), ('down', 'Down'), ('neutral', 'Neutral')
    ])
    status = models.CharField(max_length=20, default='on_track', choices=[
        ('on_track', 'On Track'), ('at_risk', 'At Risk'), ('off_track', 'Off Track'), ('exceeded', 'Exceeded')
    ])
    last_calculated = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['company', 'kpi']
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.company.name} - {self.kpi.name}"

class KPIHistory(models.Model):
    company_kpi = models.ForeignKey(CompanyKPI, on_delete=models.CASCADE, related_name='history')
    value = models.DecimalField(max_digits=15, decimal_places=4)
    recorded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-recorded_at']
        verbose_name = 'KPI History'
        verbose_name_plural = 'KPI Histories'

class DashboardWidget(models.Model):
    WIDGET_TYPES = [
        ('chart_line', 'Line Chart'), ('chart_bar', 'Bar Chart'), ('chart_pie', 'Pie Chart'),
        ('metric', 'Metric'), ('table', 'Table'), ('gauge', 'Gauge'), ('list', 'List')
    ]
    from apps.core.models import Company
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='dashboard_widgets')
    title = models.CharField(max_length=255)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES, default='metric')
    data_source = models.CharField(max_length=255, blank=True)
    config = models.JSONField(default=dict, blank=True)
    position_x = models.PositiveIntegerField(default=0)
    position_y = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(default=4)
    height = models.PositiveIntegerField(default=4)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position_y', 'position_x']
