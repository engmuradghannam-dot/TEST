"""
BI / OLAP Layer for Nexus SaaS
Business Intelligence, OLAP Cubes, Financial Analytics
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import JSONField
import logging

logger = logging.getLogger(__name__)


class OLAPCube(models.Model):
    """OLAP Cube Definition"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name=_('Name'))
    slug = models.SlugField(max_length=200, unique=True, verbose_name=_('Slug'))
    description = models.TextField(blank=True, verbose_name=_('Description'))

    # Cube structure
    dimensions = models.JSONField(default=list, verbose_name=_('Dimensions'))
    measures = models.JSONField(default=list, verbose_name=_('Measures'))

    # Data source
    source_model = models.CharField(max_length=200, verbose_name=_('Source Model'))
    source_query = models.TextField(blank=True, verbose_name=_('Source Query'))

    # Aggregation
    aggregation_function = models.CharField(max_length=50, default='SUM', verbose_name=_('Aggregation'))

    # Cache
    cache_duration_minutes = models.PositiveIntegerField(default=60, verbose_name=_('Cache Duration'))
    last_refreshed = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('OLAP Cube')
        verbose_name_plural = _('OLAP Cubes')


class BIReport(models.Model):
    """Business Intelligence Report"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name=_('Name'))
    slug = models.SlugField(max_length=200, unique=True, verbose_name=_('Slug'))
    description = models.TextField(blank=True, verbose_name=_('Description'))

    class ReportType(models.TextChoices):
        TABLE = 'table', _('Table')
        CHART = 'chart', _('Chart')
        DASHBOARD = 'dashboard', _('Dashboard')
        PIVOT = 'pivot', _('Pivot Table')
        KPI = 'kpi', _('KPI')
        MAP = 'map', _('Map')

    report_type = models.CharField(max_length=20, choices=ReportType.choices, verbose_name=_('Report Type'))

    # Data configuration
    data_source = models.CharField(max_length=200, verbose_name=_('Data Source'))
    filters = models.JSONField(default=dict, blank=True, verbose_name=_('Filters'))
    columns = models.JSONField(default=list, verbose_name=_('Columns'))

    # Visualization config
    chart_type = models.CharField(max_length=50, blank=True, verbose_name=_('Chart Type'))
    visualization_config = models.JSONField(default=dict, blank=True, verbose_name=_('Visualization Config'))

    # Sharing
    is_public = models.BooleanField(default=False, verbose_name=_('Is Public'))
    shared_with = models.JSONField(default=list, blank=True, verbose_name=_('Shared With'))

    # Schedule
    is_scheduled = models.BooleanField(default=False, verbose_name=_('Is Scheduled'))
    schedule_cron = models.CharField(max_length=100, blank=True, verbose_name=_('Schedule Cron'))
    last_run = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey('tenants.TenantUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('BI Report')
        verbose_name_plural = _('BI Reports')


class BIDashboard(models.Model):
    """BI Dashboard"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name=_('Name'))
    slug = models.SlugField(max_length=200, unique=True, verbose_name=_('Slug'))
    description = models.TextField(blank=True, verbose_name=_('Description'))

    # Layout
    layout = models.JSONField(default=dict, verbose_name=_('Layout'))
    widgets = models.JSONField(default=list, verbose_name=_('Widgets'))

    # Reports on dashboard
    reports = models.ManyToManyField(BIReport, blank=True, related_name='dashboards')

    # Sharing
    is_default = models.BooleanField(default=False, verbose_name=_('Is Default'))
    is_public = models.BooleanField(default=False, verbose_name=_('Is Public'))

    created_by = models.ForeignKey('tenants.TenantUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('BI Dashboard')
        verbose_name_plural = _('BI Dashboards')


class FinancialAnalytics(models.Model):
    """Financial Analytics & KPIs"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Period
    period_start = models.DateField(verbose_name=_('Period Start'))
    period_end = models.DateField(verbose_name=_('Period End'))
    period_type = models.CharField(max_length=20, default='monthly', verbose_name=_('Period Type'))

    # Revenue
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_('Total Revenue'))
    recurring_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_('Recurring Revenue'))
    new_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_('New Revenue'))

    # Expenses
    total_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_('Total Expenses'))
    cogs = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_('COGS'))
    operating_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_('Operating Expenses'))

    # Metrics
    gross_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_('Gross Profit'))
    net_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_('Net Profit'))
    gross_margin = models.FloatField(default=0, verbose_name=_('Gross Margin %'))
    net_margin = models.FloatField(default=0, verbose_name=_('Net Margin %'))

    # SaaS Metrics
    mrr = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_('MRR'))
    arr = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_('ARR'))
    churn_rate = models.FloatField(default=0, verbose_name=_('Churn Rate %'))
    ltv = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_('LTV'))
    cac = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_('CAC'))
    ltv_cac_ratio = models.FloatField(default=0, verbose_name=_('LTV/CAC Ratio'))

    # Breakdown
    revenue_by_product = models.JSONField(default=dict, verbose_name=_('Revenue by Product'))
    revenue_by_region = models.JSONField(default=dict, verbose_name=_('Revenue by Region'))
    revenue_by_channel = models.JSONField(default=dict, verbose_name=_('Revenue by Channel'))

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-period_end']
        unique_together = ['period_start', 'period_end', 'period_type']
        verbose_name = _('Financial Analytics')
        verbose_name_plural = _('Financial Analytics')


class DataWarehouseSync(models.Model):
    """Data Warehouse Synchronization"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    table_name = models.CharField(max_length=200, verbose_name=_('Table Name'))
    last_sync = models.DateTimeField(null=True, blank=True)
    records_synced = models.PositiveIntegerField(default=0)
    sync_status = models.CharField(max_length=20, default='pending')
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-last_sync']
        verbose_name = _('Data Warehouse Sync')
        verbose_name_plural = _('Data Warehouse Syncs')
