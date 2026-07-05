from rest_framework import viewsets
from .models import (
    Item, ItemGroup, StockEntry, ItemSerialNumber, ItemBatch,
    StockReconciliation, StockReconciliationItem,
)
from .serializers import (
    ItemSerializer, ItemGroupSerializer, StockEntrySerializer,
    ItemSerialNumberSerializer, ItemBatchSerializer,
    StockReconciliationSerializer, StockReconciliationItemSerializer,
)
from apps.core.mixins import CompanyScopedMixin


class ItemViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    company_field = 'company'


class ItemGroupViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = ItemGroup.objects.all()
    serializer_class = ItemGroupSerializer
    company_field = 'company'


class StockEntryViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = StockEntry.objects.all()
    serializer_class = StockEntrySerializer
    company_field = 'company'


class ItemSerialNumberViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = ItemSerialNumber.objects.all()
    serializer_class = ItemSerialNumberSerializer
    filterset_fields = ['item', 'status']
    company_field = 'item__company'


class ItemBatchViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = ItemBatch.objects.all()
    serializer_class = ItemBatchSerializer
    filterset_fields = ['item']
    company_field = 'item__company'


class StockReconciliationViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = StockReconciliation.objects.all()
    serializer_class = StockReconciliationSerializer
    filterset_fields = ['warehouse', 'status', 'reason']
    company_field = 'company'


class StockReconciliationItemViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = StockReconciliationItem.objects.all()
    serializer_class = StockReconciliationItemSerializer
    filterset_fields = ['reconciliation', 'item']
    company_field = 'reconciliation__company'
