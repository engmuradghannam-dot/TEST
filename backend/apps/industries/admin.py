from django.contrib import admin
from .models import (
    IndustryCatalog, IndustryControl, AIAgentRegistry,
    CompanyIndustryProfile, ControlExecutionLog
)

@admin.register(IndustryCatalog)
class IndustryCatalogAdmin(admin.ModelAdmin):
    list_display = ['industry_id', 'name', 'category', 'is_active', 'is_premium', 'required_license_tier']
    list_filter = ['category', 'is_active', 'is_premium', 'required_license_tier']
    search_fields = ['name', 'name_ar', 'industry_id']
    ordering = ['sort_order', 'name']

@admin.register(IndustryControl)
class IndustryControlAdmin(admin.ModelAdmin):
    list_display = ['control_id', 'control_name', 'industry', 'control_type', 'is_required', 'severity']
    list_filter = ['control_type', 'is_required', 'severity', 'compliance_framework']
    search_fields = ['control_id', 'control_name', 'description']
    list_select_related = ['industry']

@admin.register(AIAgentRegistry)
class AIAgentRegistryAdmin(admin.ModelAdmin):
    list_display = ['agent_id', 'name', 'industry', 'agent_type', 'is_active', 'usage_count']
    list_filter = ['agent_type', 'is_active']
    search_fields = ['agent_id', 'name', 'description']

@admin.register(CompanyIndustryProfile)
class CompanyIndustryProfileAdmin(admin.ModelAdmin):
    list_display = ['company', 'industry', 'is_primary', 'is_active', 'compliance_score', 'maturity_level']
    list_filter = ['is_primary', 'is_active', 'maturity_level']
    filter_horizontal = ['activated_controls', 'activated_agents']

@admin.register(ControlExecutionLog)
class ControlExecutionLogAdmin(admin.ModelAdmin):
    list_display = ['control', 'company', 'status', 'risk_level', 'executed_at']
    list_filter = ['status', 'risk_level']
    readonly_fields = ['executed_at', 'completed_at']
