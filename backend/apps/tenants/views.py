"""
API Views for tenant management.
"""
import logging
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_tenants.utils import schema_context
from django.db import transaction
from .models import Tenant, Domain, TenantUser, TenantMembership, TenantSettings
from .serializers import (
    TenantSerializer, DomainSerializer, TenantUserSerializer,
    TenantMembershipSerializer, TenantSettingsSerializer, TenantCreateSerializer
)
from apps.core.permissions import IsTenantOwner, IsTenantAdmin

logger = logging.getLogger(__name__)


class TenantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for tenant CRUD operations.
    """
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return tenants the user has access to."""
        return Tenant.objects.filter(
            memberships__user=self.request.user,
            memberships__is_active=True
        ).distinct()

    def get_permissions(self):
        if self.action in ['create']:
            return [permissions.AllowAny()]
        if self.action in ['destroy', 'update_partial']:
            return [IsTenantOwner()]
        return [permissions.IsAuthenticated()]

    def create(self, request):
        """Create a new tenant with owner user."""
        serializer = TenantCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            # Create tenant
            tenant = Tenant.objects.create(
                name=data['name'],
                slug=data['slug'],
                schema_name=data['slug'],
                status=Tenant.Status.TRIAL,
                on_trial=True,
            )

            # Create domain
            base_domain = request.get_host().split(':')[0]
            if '.' in base_domain:
                base_domain = '.'.join(base_domain.split('.')[1:])

            Domain.objects.create(
                tenant=tenant,
                domain=f"{data['slug']}.{base_domain}",
                is_primary=True,
                domain_type=Domain.DomainType.SUBDOMAIN
            )

            # Create owner user in tenant schema
            with schema_context(tenant.schema_name):
                owner = TenantUser.objects.create_user(
                    email=data['owner_email'],
                    password=data['owner_password'],
                    first_name=data['owner_first_name'],
                    last_name=data['owner_last_name'],
                    is_verified=True
                )

            # Create membership in public schema
            TenantMembership.objects.create(
                user=owner,
                tenant=tenant,
                role=TenantMembership.Role.OWNER,
                is_active=True
            )

            logger.info(f"Tenant created: {tenant.schema_name} by {data['owner_email']}")

            return Response(
                TenantSerializer(tenant).data,
                status=status.HTTP_201_CREATED
            )

    @action(detail=True, methods=['post'])
    def switch(self, request, pk=None):
        """Switch to a tenant context."""
        tenant = self.get_object()
        membership = tenant.memberships.filter(user=request.user, is_active=True).first()

        if not membership:
            return Response(
                {'error': 'You do not have access to this tenant.'},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response({
            'tenant': TenantSerializer(tenant).data,
            'role': membership.role,
            'permissions': membership.permissions
        })

    @action(detail=True, methods=['post'])
    def invite_member(self, request, pk=None):
        """Invite a user to the tenant."""
        tenant = self.get_object()
        email = request.data.get('email')
        role = request.data.get('role', TenantMembership.Role.MEMBER)

        # Check user limit
        current_users = tenant.memberships.filter(is_active=True).count()
        if current_users >= tenant.max_users:
            return Response(
                {'error': 'User limit exceeded. Upgrade your plan.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Create or get user
        user, created = TenantUser.objects.get_or_create(
            email=email,
            defaults={
                'first_name': '',
                'last_name': '',
                'is_active': True
            }
        )

        membership, created = TenantMembership.objects.get_or_create(
            user=user,
            tenant=tenant,
            defaults={
                'role': role,
                'is_active': True,
                'invited_by': request.user
            }
        )

        if not created:
            return Response(
                {'error': 'User is already a member of this tenant.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Send invitation email (async)
        # TODO: Add Celery task

        return Response(
            TenantMembershipSerializer(membership).data,
            status=status.HTTP_201_CREATED
        )


class DomainViewSet(viewsets.ModelViewSet):
    """ViewSet for domain management."""
    serializer_class = DomainSerializer
    permission_classes = [IsTenantAdmin]

    def get_queryset(self):
        return Domain.objects.filter(tenant=self.request.tenant)

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)


class TenantMembershipViewSet(viewsets.ModelViewSet):
    """ViewSet for membership management."""
    serializer_class = TenantMembershipSerializer
    permission_classes = [IsTenantAdmin]

    def get_queryset(self):
        return TenantMembership.objects.filter(tenant=self.request.tenant)

    @action(detail=True, methods=['post'])
    def update_role(self, request, pk=None):
        """Update member role."""
        membership = self.get_object()
        new_role = request.data.get('role')

        if new_role not in [r[0] for r in TenantMembership.Role.choices]:
            return Response(
                {'error': 'Invalid role.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        membership.role = new_role
        membership.save()

        return Response(TenantMembershipSerializer(membership).data)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a member."""
        membership = self.get_object()
        membership.is_active = False
        membership.save()
        return Response(TenantMembershipSerializer(membership).data)


class TenantSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet for tenant settings."""
    serializer_class = TenantSettingsSerializer
    permission_classes = [IsTenantAdmin]

    def get_object(self):
        return TenantSettings.objects.get_or_create(tenant=self.request.tenant)[0]

    def get_queryset(self):
        return TenantSettings.objects.filter(tenant=self.request.tenant)
