
from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from .models import Tenant, Domain, TenantUser, TenantMembership, TenantSettings


@admin.register(Tenant)
class TenantAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'schema_name', 'status', 'plan', 'paid_until', 'created_at']
    list_filter = ['status', 'plan', 'on_trial', 'created_at']
    search_fields = ['name', 'schema_name', 'slug']
    readonly_fields = ['schema_name', 'created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'schema_name', 'status')
        }),
        ('Billing', {
            'fields': ('plan', 'paid_until', 'on_trial', 'trial_end_date')
        }),
        ('Limits', {
            'fields': ('max_users', 'max_storage_mb')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'tenant', 'is_primary', 'domain_type', 'ssl_enabled', 'created_at']
    list_filter = ['domain_type', 'is_primary', 'ssl_enabled', 'created_at']
    search_fields = ['domain', 'tenant__name']


@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_active', 'is_verified', 'date_joined']
    list_filter = ['is_active', 'is_verified', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name']
    readonly_fields = ['date_joined', 'last_login']


@admin.register(TenantMembership)
class TenantMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'tenant', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['user__email', 'tenant__name']


@admin.register(TenantSettings)
class TenantSettingsAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'company_name', 'require_2fa', 'created_at']
    search_fields = ['tenant__name', 'company_name']
