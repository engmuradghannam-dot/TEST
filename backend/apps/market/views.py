from rest_framework import viewsets, permissions
from .models import CertificationRecord, Partner, MarketplaceApp, CountryLocalization
from .serializers import (CertificationRecordSerializer, PartnerSerializer,
                           MarketplaceAppSerializer, CountryLocalizationSerializer)
from apps.core.mixins import CompanyScopedMixin


class CertificationRecordViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = CertificationRecord.objects.all()
    serializer_class = CertificationRecordSerializer
    permission_classes = [permissions.IsAuthenticated]


class PartnerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Partner.objects.filter(is_active=True)
    serializer_class = PartnerSerializer
    permission_classes = [permissions.IsAuthenticated]


class MarketplaceAppViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MarketplaceApp.objects.filter(is_active=True)
    serializer_class = MarketplaceAppSerializer
    permission_classes = [permissions.IsAuthenticated]


class CountryLocalizationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CountryLocalization.objects.all()
    serializer_class = CountryLocalizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['country']
