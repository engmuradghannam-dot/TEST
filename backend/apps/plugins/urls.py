from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'plugins', views.PluginViewSet, basename='plugin')
router.register(r'tenant-plugins', views.TenantPluginViewSet, basename='tenant-plugin')
router.register(r'hooks', views.PluginHookViewSet, basename='hook')

urlpatterns = [
    path('', include(router.urls)),
]
