from django.urls import path
from apps.iam import views

urlpatterns = [
    path('nl/', views.NaturalLanguageView.as_view()),
    path('forecast/sales/', views.SalesForecastView.as_view()),
    path('core/health/', views.AICoreHealthView.as_view()),
    path('security/scan/', views.SecurityScanView.as_view()),
]
