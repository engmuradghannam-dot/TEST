from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import Supplier, PurchaseOrder, PurchaseOrderItem, PurchaseTaxCharge, PurchasePayment
from .serializers import (
    SupplierSerializer, PurchaseOrderSerializer, PurchaseOrderItemSerializer,
    PurchaseTaxChargeSerializer, PurchasePaymentSerializer,
)
from apps.core.mixins import CompanyScopedMixin, LockAfterSubmitMixin


class SupplierViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name', 'email', 'tax_id']
    filterset_fields = ['company', 'is_active']
    company_field = 'company'


class PurchaseOrderViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['po_number', 'supplier__name']
    filterset_fields = ['status', 'company', 'supplier']
    company_field = 'company'


class PurchaseOrderItemViewSet(LockAfterSubmitMixin, CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = PurchaseOrderItem.objects.all()
    serializer_class = PurchaseOrderItemSerializer
    filterset_fields = ['purchase_order', 'item']
    company_field = 'purchase_order__company'
    parent_field = 'purchase_order'


class PurchaseTaxChargeViewSet(LockAfterSubmitMixin, CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = PurchaseTaxCharge.objects.all()
    serializer_class = PurchaseTaxChargeSerializer
    filterset_fields = ['purchase_order']
    company_field = 'purchase_order__company'
    parent_field = 'purchase_order'


class PurchasePaymentViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = PurchasePayment.objects.all()
    serializer_class = PurchasePaymentSerializer
    filterset_fields = ['purchase_order']
    company_field = 'purchase_order__company'
