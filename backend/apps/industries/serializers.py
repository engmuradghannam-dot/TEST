from rest_framework import serializers
from .models import (
    IndustryCatalog, IndustryControl, AIAgentRegistry,
    CompanyIndustryProfile, ControlExecutionLog
)

class IndustryCatalogSerializer(serializers.ModelSerializer):
    control_count = serializers.SerializerMethodField()
    agent_count = serializers.SerializerMethodField()

    class Meta:
        model = IndustryCatalog
        fields = '__all__'

    def get_control_count(self, obj):
        return obj.controls.filter(is_active=True).count()

    def get_agent_count(self, obj):
        return obj.ai_agents.filter(is_active=True).count()


class IndustryControlSerializer(serializers.ModelSerializer):
    industry_name = serializers.CharField(source='industry.name', read_only=True)
    industry_id = serializers.CharField(source='industry.industry_id', read_only=True)

    class Meta:
        model = IndustryControl
        fields = '__all__'


class IndustryControlSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = IndustryControl
        fields = ['control_id', 'control_name', 'control_type', 'is_required', 'severity', 'kpi_name', 'compliance_framework']


class AIAgentRegistrySerializer(serializers.ModelSerializer):
    industry_name = serializers.CharField(source='industry.name', read_only=True)

    class Meta:
        model = AIAgentRegistry
        fields = '__all__'


class CompanyIndustryProfileSerializer(serializers.ModelSerializer):
    industry_name = serializers.CharField(source='industry.name', read_only=True)
    industry_id = serializers.CharField(source='industry.industry_id', read_only=True)
    control_count = serializers.SerializerMethodField()
    agent_count = serializers.SerializerMethodField()
    activated_control_ids = serializers.SerializerMethodField()

    class Meta:
        model = CompanyIndustryProfile
        fields = '__all__'

    def get_control_count(self, obj):
        return obj.activated_controls.count()

    def get_agent_count(self, obj):
        return obj.activated_agents.count()

    def get_activated_control_ids(self, obj):
        return list(obj.activated_controls.values_list('control_id', flat=True))


class ControlExecutionLogSerializer(serializers.ModelSerializer):
    control_name = serializers.CharField(source='control.control_name', read_only=True)
    control_id = serializers.CharField(source='control.control_id', read_only=True)
    executed_by_name = serializers.CharField(source='executed_by.email', read_only=True)

    class Meta:
        model = ControlExecutionLog
        fields = '__all__'
        read_only_fields = ['executed_at', 'completed_at']
