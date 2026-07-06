from rest_framework import viewsets
from .models import WorkOrder, BOM, BOMItem
from .serializers import WorkOrderSerializer, BOMSerializer, BOMItemSerializer
from apps.core.mixins import CompanyScopedMixin


class WorkOrderViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = WorkOrder.objects.all()
    serializer_class = WorkOrderSerializer
    company_field = 'company'


class BOMViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = BOM.objects.all()
    serializer_class = BOMSerializer
    company_field = 'company'


class BOMItemViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = BOMItem.objects.all()
    serializer_class = BOMItemSerializer
    filterset_fields = ['bom', 'item']
    company_field = 'bom__company'
