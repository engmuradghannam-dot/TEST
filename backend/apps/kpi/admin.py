from django.contrib import admin
from .models import KPIDefinition, CompanyKPI, KPIHistory, DashboardWidget

@admin.register(KPIDefinition)
class KPIDefinitionAdmin(admin.ModelAdmin):
    list_display = ['kpi_id', 'name', 'category', 'frequency', 'is_active']
    list_filter = ['category', 'frequency', 'is_active']
    search_fields = ['name', 'kpi_id']

@admin.register(CompanyKPI)
class CompanyKPIAdmin(admin.ModelAdmin):
    list_display = ['company', 'kpi', 'current_value', 'status', 'trend', 'last_calculated']
    list_filter = ['status', 'trend', 'is_active']

@admin.register(KPIHistory)
class KPIHistoryAdmin(admin.ModelAdmin):
    list_display = ['company_kpi', 'value', 'recorded_at']
    ordering = ['-recorded_at']

@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'widget_type', 'position_x', 'position_y', 'is_active']
    list_filter = ['widget_type', 'is_active']
