from rest_framework import serializers
from .models import (
    ComplianceFramework, ComplianceRequirement, CompanyCompliance,
    ComplianceAudit, RegulatoryUpdate
)

class ComplianceFrameworkSerializer(serializers.ModelSerializer):
    requirement_count = serializers.SerializerMethodField()

    class Meta:
        model = ComplianceFramework
        fields = '__all__'

    def get_requirement_count(self, obj):
        return obj.requirements.filter(is_active=True).count()


class ComplianceRequirementSerializer(serializers.ModelSerializer):
    framework_name = serializers.CharField(source='framework.name', read_only=True)

    class Meta:
        model = ComplianceRequirement
        fields = '__all__'


class CompanyComplianceSerializer(serializers.ModelSerializer):
    framework_name = serializers.CharField(source='framework.name', read_only=True)
    framework_id = serializers.CharField(source='framework.framework_id', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    audit_count = serializers.SerializerMethodField()
    pass_rate = serializers.SerializerMethodField()

    class Meta:
        model = CompanyCompliance
        fields = '__all__'

    def get_audit_count(self, obj):
        return obj.audits.count()

    def get_pass_rate(self, obj):
        total = obj.audits.count()
        if total == 0:
            return 0
        passed = obj.audits.filter(result='pass').count()
        return round((passed / total) * 100, 2)


class ComplianceAuditSerializer(serializers.ModelSerializer):
    requirement_title = serializers.CharField(source='requirement.title', read_only=True)
    requirement_id = serializers.CharField(source='requirement.requirement_id', read_only=True)
    auditor_name = serializers.CharField(source='auditor.email', read_only=True)

    class Meta:
        model = ComplianceAudit
        fields = '__all__'


class RegulatoryUpdateSerializer(serializers.ModelSerializer):
    framework_name = serializers.CharField(source='framework.name', read_only=True)

    class Meta:
        model = RegulatoryUpdate
        fields = '__all__'
