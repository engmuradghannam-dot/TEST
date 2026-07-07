from rest_framework.routers import DefaultRouter
from .views import (CertificationRecordViewSet, PartnerViewSet,
                    MarketplaceAppViewSet, CountryLocalizationViewSet)

router = DefaultRouter()
router.register(r'certifications', CertificationRecordViewSet)
router.register(r'partners', PartnerViewSet, basename='partner')
router.register(r'apps', MarketplaceAppViewSet, basename='marketplace-app')
router.register(r'localizations', CountryLocalizationViewSet, basename='localization')

urlpatterns = router.urls
