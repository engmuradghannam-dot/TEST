
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from .models import Plan, Subscription, Invoice, Payment
from .serializers import PlanSerializer, SubscriptionSerializer, InvoiceSerializer, PaymentSerializer
from .stripe_client import (
    create_stripe_customer, create_stripe_subscription,
    handle_stripe_webhook
)


class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.filter(is_active=True, is_public=True)
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(tenant=self.request.tenant)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        subscription = self.get_object()
        subscription.cancel()
        return Response({'status': 'Subscription will be cancelled at period end'})

    @action(detail=True, methods=['post'])
    def reactivate(self, request, pk=None):
        subscription = self.get_object()
        subscription.reactivate()
        return Response({'status': 'Subscription reactivated'})


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Invoice.objects.filter(tenant=self.request.tenant)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(tenant=self.request.tenant)


@api_view(['POST'])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = request.settings.STRIPE_WEBHOOK_SECRET

    try:
        event = handle_stripe_webhook(payload, sig_header, webhook_secret)
        return Response({'status': 'success'})
    except Exception as e:
        return Response({'error': str(e)}, status=400)
