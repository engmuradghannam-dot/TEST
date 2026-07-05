from rest_framework import viewsets
from .models import Asset, AssetCategory
from .serializers import AssetSerializer, AssetCategorySerializer
from apps.core.mixins import CompanyScopedMixin


class AssetViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    company_field = 'company'


class AssetCategoryViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = AssetCategory.objects.all()
    serializer_class = AssetCategorySerializer
    company_field = 'company'
