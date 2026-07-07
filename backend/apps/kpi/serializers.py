from rest_framework import serializers
from .models import KPIDefinition, CompanyKPI, KPIHistory, DashboardWidget

class KPIDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = KPIDefinition
        fields = '__all__'

class KPIHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = KPIHistory
        fields = '__all__'

class CompanyKPISerializer(serializers.ModelSerializer):
    kpi_name = serializers.CharField(source='kpi.name', read_only=True)
    kpi_id = serializers.CharField(source='kpi.kpi_id', read_only=True)
    kpi_category = serializers.CharField(source='kpi.category', read_only=True)
    kpi_unit = serializers.CharField(source='kpi.unit', read_only=True)
    target_value = serializers.DecimalField(source='kpi.target_value', max_digits=15, decimal_places=4, read_only=True)
    history = KPIHistorySerializer(many=True, read_only=True)

    class Meta:
        model = CompanyKPI
        fields = '__all__'

class DashboardWidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardWidget
        fields = '__all__'
