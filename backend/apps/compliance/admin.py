from django.contrib import admin
from .models import (
    ComplianceFramework, ComplianceRequirement, CompanyCompliance,
    ComplianceAudit, RegulatoryUpdate
)

@admin.register(ComplianceFramework)
class ComplianceFrameworkAdmin(admin.ModelAdmin):
    list_display = ['framework_id', 'name', 'category', 'is_active', 'effective_date']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'framework_id']

@admin.register(ComplianceRequirement)
class ComplianceRequirementAdmin(admin.ModelAdmin):
    list_display = ['requirement_id', 'title', 'framework', 'severity', 'is_active']
    list_filter = ['severity', 'is_active']
    search_fields = ['title', 'requirement_id']

@admin.register(CompanyCompliance)
class CompanyComplianceAdmin(admin.ModelAdmin):
    list_display = ['company', 'framework', 'status', 'compliance_score', 'last_assessment_date']
    list_filter = ['status', 'is_active']

@admin.register(ComplianceAudit)
class ComplianceAuditAdmin(admin.ModelAdmin):
    list_display = ['requirement', 'company_compliance', 'result', 'audit_date', 'remediation_required']
    list_filter = ['result', 'remediation_required', 'remediation_status']

@admin.register(RegulatoryUpdate)
class RegulatoryUpdateAdmin(admin.ModelAdmin):
    list_display = ['title', 'framework', 'impact_level', 'effective_date', 'is_read']
    list_filter = ['impact_level', 'is_read']
