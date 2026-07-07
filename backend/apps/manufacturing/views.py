from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import WorkOrder, BOM, BOMItem
from .serializers import WorkOrderSerializer, BOMSerializer, BOMItemSerializer
from apps.core.mixins import CompanyScopedMixin
from apps.inventory.models import Item


class WorkOrderViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = WorkOrder.objects.all()
    serializer_class = WorkOrderSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'bom', 'company']
    company_field = 'company'

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start production with concurrency protection."""
        with transaction.atomic():
            # Lock the work order row to prevent race conditions
            work_order = get_object_or_404(
                WorkOrder.objects.select_for_update(),
                pk=pk
            )

            if work_order.status != 'Draft':
                return Response(
                    {'error': 'Work order must be in Draft status to start.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            work_order.status = 'In Progress'
            work_order.save()

        return Response(WorkOrderSerializer(work_order).data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete production with stock validation and concurrency protection."""
        with transaction.atomic():
            # Lock the work order and related BOM items
            work_order = get_object_or_404(
                WorkOrder.objects.select_for_update(),
                pk=pk
            )

            if work_order.status != 'In Progress':
                return Response(
                    {'error': 'Work order must be In Progress to complete.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            bom = work_order.bom
            if not bom:
                return Response(
                    {'error': 'Work order has no BOM.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate stock availability with locking
            insufficient = []
            for item in bom.items.select_related('item').select_for_update():
                if item.item.stock_qty < item.qty:
                    insufficient.append({
                        'item': item.item.item_name,
                        'required': item.qty,
                        'available': item.item.stock_qty
                    })

            if insufficient:
                return Response(
                    {'error': 'Insufficient stock', 'details': insufficient},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Deduct stock (locked rows prevent double-spending)
            for item in bom.items.select_related('item'):
                item.item.stock_qty -= item.qty
                item.item.save()

            work_order.status = 'Completed'
            work_order.save()

        return Response(WorkOrderSerializer(work_order).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel work order with concurrency protection."""
        with transaction.atomic():
            work_order = get_object_or_404(
                WorkOrder.objects.select_for_update(),
                pk=pk
            )

            if work_order.status == 'Completed':
                return Response(
                    {'error': 'Cannot cancel a completed work order.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            work_order.status = 'Cancelled'
            work_order.save()

        return Response(WorkOrderSerializer(work_order).data)


class BOMViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = BOM.objects.all()
    serializer_class = BOMSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['item', 'is_active', 'company']
    company_field = 'company'


class BOMItemViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = BOMItem.objects.all()
    serializer_class = BOMItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['bom', 'item']
    company_field = 'bom__company'
