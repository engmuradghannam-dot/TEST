
"""
Tenant-aware middleware for subdomain routing and tenant validation.
"""
import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django_tenants.middleware import TenantMainMiddleware
from django_tenants.utils import get_tenant_model
from django.core.exceptions import DisallowedHost
from django.conf import settings

logger = logging.getLogger(__name__)
TenantModel = get_tenant_model()


class NexusTenantMiddleware(TenantMainMiddleware):
    """
    Extended tenant middleware with:
    - Custom domain support
    - Tenant status validation
    - Plan limit enforcement
    - Security headers
    """

    def process_request(self, request):
        # Get hostname from request
        hostname = self.hostname_from_request(request)

        # Check if it's a public domain
        if hostname in settings.PUBLIC_DOMAINS:
            request.tenant = None
            return self.get_response(request)

        # Find tenant by domain
        try:
            domain = self.get_tenant_domain_model().objects.select_related('tenant').get(
                domain=hostname
            )
            tenant = domain.tenant
        except self.get_tenant_domain_model().DoesNotExist:
            logger.warning(f"No tenant found for domain: {hostname}")
            return self._tenant_not_found_response(request)

        # Validate tenant status
        if not tenant.is_active_tenant():
            logger.warning(f"Tenant {tenant.schema_name} is not active")
            return self._tenant_inactive_response(request, tenant)

        # Set tenant on request
        request.tenant = tenant

        # Continue with default tenant middleware behavior
        connection = self.get_tenant_database_connection()
        connection.set_tenant(tenant)

        # Add tenant context to request
        request.tenant_id = str(tenant.id)
        request.tenant_schema = tenant.schema_name
        request.tenant_plan = tenant.plan.slug if tenant.plan else 'free'

        return self.get_response(request)

    def _tenant_not_found_response(self, request):
        """Return response when tenant is not found."""
        if request.path.startswith('/api/'):
            return JsonResponse({
                'error': 'Tenant not found',
                'message': 'The requested domain does not belong to any tenant.'
            }, status=404)
        return self.get_response(request)

    def _tenant_inactive_response(self, request, tenant):
        """Return response when tenant is inactive."""
        if tenant.status == tenant.Status.SUSPENDED:
            status_code = 403
            message = 'Your account has been suspended. Please contact support.'
        elif tenant.status == tenant.Status.CANCELLED:
            status_code = 403
            message = 'Your account has been cancelled.'
        else:
            status_code = 403
            message = 'Your account is not active.'

        if request.path.startswith('/api/'):
            return JsonResponse({
                'error': 'Tenant inactive',
                'message': message,
                'status': tenant.status
            }, status=status_code)
        return self.get_response(request)


class TenantLimitMiddleware(MiddlewareMixin):
    """
    Enforce tenant plan limits (users, storage, API calls).
    """

    def process_request(self, request):
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return None

        # Check user limit
        if hasattr(request, 'user') and request.user.is_authenticated:
            current_users = tenant.memberships.filter(is_active=True).count()
            if current_users >= tenant.max_users:
                # Only allow read operations for non-owners
                membership = tenant.memberships.filter(user=request.user).first()
                if membership and membership.role != TenantMembership.Role.OWNER:
                    if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                        return JsonResponse({
                            'error': 'Plan limit exceeded',
                            'message': f'Maximum {tenant.max_users} users reached. Upgrade your plan.',
                            'code': 'USER_LIMIT_EXCEEDED'
                        }, status=403)

        return None


class TenantSecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers specific to tenant context.
    """

    def process_response(self, request, response):
        tenant = getattr(request, 'tenant', None)

        if tenant:
            # Add tenant-specific security headers
            response['X-Tenant-ID'] = str(tenant.id)
            response['X-Tenant-Schema'] = tenant.schema_name

            # Content Security Policy per tenant
            csp = "default-src 'self'; "
            if tenant.settings and tenant.settings.features_enabled.get('external_embeds'):
                csp += "frame-src 'self' https:; "
            response['Content-Security-Policy'] = csp

        return response
