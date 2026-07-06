from rest_framework import permissions


class IsTenantOwner(permissions.BasePermission):
    """Allow only tenant owners."""
    def has_permission(self, request, view):
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return False
        membership = tenant.memberships.filter(user=request.user, is_active=True).first()
        return membership and membership.role == 'owner'


class IsTenantAdmin(permissions.BasePermission):
    """Allow tenant owners and admins."""
    def has_permission(self, request, view):
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return False
        membership = tenant.memberships.filter(user=request.user, is_active=True).first()
        return membership and membership.role in ['owner', 'admin']


class IsTenantManager(permissions.BasePermission):
    """Allow owners, admins, and managers."""
    def has_permission(self, request, view):
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return False
        membership = tenant.memberships.filter(user=request.user, is_active=True).first()
        return membership and membership.role in ['owner', 'admin', 'manager']


class HasTenantPermission(permissions.BasePermission):
    """Check specific permission from membership."""
    def __init__(self, permission):
        self.permission = permission

    def has_permission(self, request, view):
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return False
        membership = tenant.memberships.filter(user=request.user, is_active=True).first()
        return membership and membership.has_permission(self.permission)
