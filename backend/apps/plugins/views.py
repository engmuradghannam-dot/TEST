from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg
from .models import Plugin, TenantPlugin, PluginHook, PluginReview, HookRegistry
from .serializers import (
    PluginSerializer, TenantPluginSerializer, 
    PluginHookSerializer, PluginReviewSerializer
)
from apps.core.permissions import IsTenantAdmin


class PluginViewSet(viewsets.ModelViewSet):
    """ViewSet for marketplace plugin management."""
    serializer_class = PluginSerializer

    def get_queryset(self):
        if self.action in ['list', 'retrieve']:
            return Plugin.objects.filter(is_published=True, status=Plugin.Status.ACTIVE)
        return Plugin.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'reviews']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    @action(detail=True, methods=['post'])
    def install(self, request, pk=None):
        """Install a plugin for the current tenant."""
        plugin = self.get_object()
        tenant = request.tenant

        # Check if already installed
        if TenantPlugin.objects.filter(tenant=tenant, plugin=plugin).exists():
            return Response(
                {'error': 'Plugin already installed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if premium and not paid
        if plugin.is_premium and plugin.price > 0:
            return Response(
                {'error': 'Payment required for this plugin.'},
                status=status.HTTP_402_PAYMENT_REQUIRED
            )

        tenant_plugin = TenantPlugin.objects.create(
            tenant=tenant,
            plugin=plugin,
            status=TenantPlugin.InstallStatus.ACTIVE
        )

        # Load plugin hooks
        plugin_instance = plugin.load_module()
        if plugin_instance and hasattr(plugin_instance, 'register_hooks'):
            plugin_instance.register_hooks()

        return Response(
            TenantPluginSerializer(tenant_plugin).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def uninstall(self, request, pk=None):
        """Uninstall a plugin from the current tenant."""
        plugin = self.get_object()
        tenant = request.tenant

        tenant_plugin = TenantPlugin.objects.filter(
            tenant=tenant, plugin=plugin
        ).first()

        if not tenant_plugin:
            return Response(
                {'error': 'Plugin not installed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        tenant_plugin.status = TenantPlugin.InstallStatus.UNINSTALLED
        tenant_plugin.save()

        # Unregister hooks
        for hook in PluginHook.objects.filter(plugin=plugin):
            HookRegistry.unregister(hook.event, hook.handler_path)

        return Response({'status': 'Plugin uninstalled.'})

    @action(detail=True, methods=['get', 'post'])
    def reviews(self, request, pk=None):
        """Get or create reviews for a plugin."""
        plugin = self.get_object()

        if request.method == 'GET':
            reviews = PluginReview.objects.filter(plugin=plugin)
            serializer = PluginReviewSerializer(reviews, many=True)
            return Response(serializer.data)

        # POST - create review
        serializer = PluginReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(plugin=plugin, user=request.user)

        # Update plugin rating
        avg_rating = PluginReview.objects.filter(plugin=plugin).aggregate(
            Avg('rating')
        )['rating__avg'] or 0
        plugin.rating = round(avg_rating, 2)
        plugin.review_count = PluginReview.objects.filter(plugin=plugin).count()
        plugin.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TenantPluginViewSet(viewsets.ModelViewSet):
    """ViewSet for tenant plugin management."""
    serializer_class = TenantPluginSerializer
    permission_classes = [IsTenantAdmin]

    def get_queryset(self):
        return TenantPlugin.objects.filter(tenant=self.request.tenant)

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """Toggle plugin active/paused status."""
        tenant_plugin = self.get_object()

        if tenant_plugin.status == TenantPlugin.InstallStatus.ACTIVE:
            tenant_plugin.status = TenantPlugin.InstallStatus.PAUSED
        else:
            tenant_plugin.status = TenantPlugin.InstallStatus.ACTIVE

        tenant_plugin.save()
        return Response(TenantPluginSerializer(tenant_plugin).data)

    @action(detail=True, methods=['post'])
    def configure(self, request, pk=None):
        """Update plugin configuration."""
        tenant_plugin = self.get_object()
        tenant_plugin.config.update(request.data.get('config', {}))
        tenant_plugin.save()
        return Response(TenantPluginSerializer(tenant_plugin).data)


class PluginHookViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing plugin hooks."""
    serializer_class = PluginHookSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return PluginHook.objects.all()

    @action(detail=False, methods=['post'])
    def trigger(self, request):
        """Manually trigger a hook event."""
        event = request.data.get('event')
        args = request.data.get('args', [])
        kwargs = request.data.get('kwargs', {})

        results = HookRegistry.trigger(event, *args, **kwargs)
        return Response({'event': event, 'results': results})
