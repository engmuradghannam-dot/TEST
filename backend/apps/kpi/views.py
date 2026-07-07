from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import KPIDefinition, CompanyKPI, KPIHistory, DashboardWidget
from .serializers import (
    KPIDefinitionSerializer, CompanyKPISerializer,
    KPIHistorySerializer, DashboardWidgetSerializer
)
from apps.core.mixins import CompanyScopedMixin

class KPIDefinitionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = KPIDefinition.objects.filter(is_active=True)
    serializer_class = KPIDefinitionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'frequency']
    search_fields = ['name', 'kpi_id', 'description']
    lookup_field = 'kpi_id'

class CompanyKPIViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = CompanyKPI.objects.all().select_related('kpi')
    serializer_class = CompanyKPISerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['kpi__category', 'status', 'trend']
    ordering_fields = ['current_value', 'last_calculated', 'updated_at']
    company_field = 'company'

    @action(detail=True, methods=['post'])
    def record_value(self, request, pk=None):
        company_kpi = self.get_object()
        value = request.data.get('value')
        if value is None:
            return Response({'error': 'value required'}, status=400)
        from decimal import Decimal
        company_kpi.previous_value = company_kpi.current_value
        company_kpi.current_value = Decimal(str(value))
        if company_kpi.previous_value:
            if company_kpi.current_value > company_kpi.previous_value:
                company_kpi.trend = 'up'
            elif company_kpi.current_value < company_kpi.previous_value:
                company_kpi.trend = 'down'
            else:
                company_kpi.trend = 'neutral'
        if company_kpi.kpi.target_value:
            if company_kpi.current_value >= company_kpi.kpi.target_value:
                company_kpi.status = 'exceeded' if company_kpi.current_value > company_kpi.kpi.target_value else 'on_track'
            elif company_kpi.kpi.min_acceptable and company_kpi.current_value < company_kpi.kpi.min_acceptable:
                company_kpi.status = 'off_track'
            else:
                company_kpi.status = 'at_risk'
        from django.utils import timezone
        company_kpi.last_calculated = timezone.now()
        company_kpi.save()
        KPIHistory.objects.create(company_kpi=company_kpi, value=company_kpi.current_value, notes=request.data.get('notes', ''))
        return Response({'success': True, 'current_value': company_kpi.current_value, 'status': company_kpi.status})

class KPIHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = KPIHistory.objects.all().select_related('company_kpi')
    serializer_class = KPIHistorySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['company_kpi']
    ordering_fields = ['recorded_at']

class DashboardWidgetViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = DashboardWidget.objects.all()
    serializer_class = DashboardWidgetSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['widget_type', 'is_active']
    ordering_fields = ['position_y', 'position_x']
    company_field = 'company'
