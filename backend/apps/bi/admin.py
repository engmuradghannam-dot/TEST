
from django.contrib import admin
from .models import OLAPCube, BIReport, BIDashboard, FinancialAnalytics, DataWarehouseSync

@admin.register(OLAPCube)
class OLAPCubeAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_model', 'aggregation_function', 'is_active']
    list_filter = ['is_active']

@admin.register(BIReport)
class BIReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'is_public', 'created_at']
    list_filter = ['report_type', 'is_public']

@admin.register(BIDashboard)
class BIDashboardAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_default', 'is_public', 'created_at']

@admin.register(FinancialAnalytics)
class FinancialAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['period_start', 'period_end', 'mrr', 'arr', 'churn_rate']
    list_filter = ['period_type']

@admin.register(DataWarehouseSync)
class DataWarehouseSyncAdmin(admin.ModelAdmin):
    list_display = ['table_name', 'last_sync', 'records_synced', 'sync_status']
