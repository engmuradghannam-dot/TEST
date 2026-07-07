from django.contrib import admin
from .models import (
    IdentityProvider, SSOConnection, SAMLRequestLog,
    RoleDefinition, RoleMiningJob, RoleMiningSuggestion, PermissionAnomaly,
    UserRoleAssignment, SeparationOfDutiesRule,
    PrivilegedAccount, PrivilegedSession, PasswordVault, VaultAccessLog,
    PrivilegedCommandPolicy, AuthenticationPolicy, UserDevice,
    SecurityEvent, AdaptiveAuthentication, LoginAttempt,
    ServiceAccount, APIKeyRotation, JITAccessRequest
)

@admin.register(IdentityProvider)
class IdentityProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider_type', 'status', 'company', 'is_global']
    list_filter = ['provider_type', 'status', 'is_global']
    search_fields = ['name']

@admin.register(RoleDefinition)
class RoleDefinitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'company', 'is_system_role', 'is_active']
    list_filter = ['category', 'is_system_role', 'is_active']
    search_fields = ['name']

@admin.register(PrivilegedAccount)
class PrivilegedAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_type', 'status', 'risk_level', 'company']
    list_filter = ['account_type', 'status', 'risk_level']
    search_fields = ['name', 'target_host']

@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'category', 'severity', 'user', 'created_at']
    list_filter = ['category', 'severity', 'investigation_status']
    readonly_fields = ['created_at']
