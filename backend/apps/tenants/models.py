
"""
Multi-tenancy models using django-tenants with TenantMixin + DomainMixin
"""
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
import uuid


class TenantManager(BaseUserManager):
    """Custom user manager for tenant-aware users."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


class Tenant(TenantMixin, models.Model):
    """
    Tenant model with django-tenants TenantMixin.
    Each tenant gets a separate PostgreSQL schema.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name=_('Tenant Name'))
    slug = models.SlugField(max_length=63, unique=True, verbose_name=_('Slug'))
    schema_name = models.CharField(max_length=63, unique=True, verbose_name=_('Schema Name'))

    # Tenant status
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        SUSPENDED = 'suspended', _('Suspended')
        TRIAL = 'trial', _('Trial')
        CANCELLED = 'cancelled', _('Cancelled')

    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.TRIAL,
        verbose_name=_('Status')
    )

    # Plan & Billing
    plan = models.ForeignKey(
        'billing.Plan', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='tenants',
        verbose_name=_('Plan')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    paid_until = models.DateField(null=True, blank=True, verbose_name=_('Paid Until'))
    on_trial = models.BooleanField(default=True, verbose_name=_('On Trial'))
    trial_end_date = models.DateField(null=True, blank=True, verbose_name=_('Trial End Date'))

    # Configuration
    auto_create_schema = True
    auto_drop_schema = False

    # Limits (enforced in middleware)
    max_users = models.PositiveIntegerField(default=5, verbose_name=_('Max Users'))
    max_storage_mb = models.PositiveIntegerField(default=100, verbose_name=_('Max Storage (MB)'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Tenant')
        verbose_name_plural = _('Tenants')

    def __str__(self):
        return f"{self.name} ({self.schema_name})"

    def is_active_tenant(self):
        """Check if tenant is active and paid."""
        if self.status == self.Status.CANCELLED:
            return False
        if self.status == self.Status.SUSPENDED:
            return False
        if self.on_trial and self.trial_end_date:
            from django.utils import timezone
            if self.trial_end_date < timezone.now().date():
                self.status = self.Status.SUSPENDED
                self.save()
                return False
        return True


class Domain(DomainMixin, models.Model):
    """
    Domain model for tenant routing using DomainMixin.
    Supports subdomain and custom domain routing.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        related_name='domains',
        verbose_name=_('Tenant')
    )
    domain = models.CharField(max_length=253, unique=True, verbose_name=_('Domain'))
    is_primary = models.BooleanField(default=False, verbose_name=_('Is Primary'))

    # Domain type
    class DomainType(models.TextChoices):
        SUBDOMAIN = 'subdomain', _('Subdomain')
        CUSTOM = 'custom', _('Custom Domain')

    domain_type = models.CharField(
        max_length=20,
        choices=DomainType.choices,
        default=DomainType.SUBDOMAIN,
        verbose_name=_('Domain Type')
    )

    # SSL/Security
    ssl_enabled = models.BooleanField(default=False, verbose_name=_('SSL Enabled'))
    ssl_cert_path = models.CharField(max_length=500, blank=True, verbose_name=_('SSL Certificate Path'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        ordering = ['-is_primary', '-created_at']
        verbose_name = _('Domain')
        verbose_name_plural = _('Domains')

    def __str__(self):
        return f"{self.domain} -> {self.tenant.name}"


class TenantUser(AbstractUser):
    """
    Custom user model that works across public and tenant schemas.
    Uses email as the primary identifier.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(max_length=150, blank=True, verbose_name=_('Username'))

    # Tenant association (for public schema users who belong to multiple tenants)
    tenants = models.ManyToManyField(
        Tenant,
        through='TenantMembership',
        related_name='users',
        blank=True,
        verbose_name=_('Tenants')
    )

    # Profile
    first_name = models.CharField(max_length=150, blank=True, verbose_name=_('First Name'))
    last_name = models.CharField(max_length=150, blank=True, verbose_name=_('Last Name'))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_('Phone'))
    avatar = models.URLField(blank=True, verbose_name=_('Avatar'))

    # Security
    is_verified = models.BooleanField(default=False, verbose_name=_('Is Verified'))
    two_factor_enabled = models.BooleanField(default=False, verbose_name=_('2FA Enabled'))
    last_ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=_('Last IP'))

    # Preferences
    language = models.CharField(max_length=10, default='en', verbose_name=_('Language'))
    timezone = models.CharField(max_length=50, default='UTC', verbose_name=_('Timezone'))

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = TenantManager()

    class Meta:
        ordering = ['-date_joined']
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def get_initials(self):
        return f"{self.first_name[0]}{self.last_name[0]}".upper() if self.first_name and self.last_name else "U"


class TenantMembership(models.Model):
    """
    Junction table for user-tenant relationship with roles and permissions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        TenantUser, 
        on_delete=models.CASCADE, 
        related_name='memberships',
        verbose_name=_('User')
    )
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        related_name='memberships',
        verbose_name=_('Tenant')
    )

    # Role system
    class Role(models.TextChoices):
        OWNER = 'owner', _('Owner')
        ADMIN = 'admin', _('Admin')
        MANAGER = 'manager', _('Manager')
        MEMBER = 'member', _('Member')
        VIEWER = 'viewer', _('Viewer')

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
        verbose_name=_('Role')
    )

    # Permissions (JSON field for flexible permission system)
    permissions = models.JSONField(default=dict, blank=True, verbose_name=_('Permissions'))

    # Status
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))
    invited_by = models.ForeignKey(
        TenantUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invited_members',
        verbose_name=_('Invited By')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        unique_together = ['user', 'tenant']
        ordering = ['-created_at']
        verbose_name = _('Tenant Membership')
        verbose_name_plural = _('Tenant Memberships')

    def __str__(self):
        return f"{self.user.email} @ {self.tenant.name} ({self.role})"

    def has_permission(self, permission):
        """Check if membership has a specific permission."""
        if self.role == self.Role.OWNER:
            return True
        perms = self.permissions or {}
        return perms.get(permission, False)


class TenantSettings(models.Model):
    """
    Per-tenant settings and configuration.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name='settings',
        verbose_name=_('Tenant')
    )

    # Branding
    company_name = models.CharField(max_length=200, blank=True, verbose_name=_('Company Name'))
    company_logo = models.URLField(blank=True, verbose_name=_('Company Logo'))
    favicon = models.URLField(blank=True, verbose_name=_('Favicon'))
    primary_color = models.CharField(max_length=7, default='#3B82F6', verbose_name=_('Primary Color'))

    # Features
    features_enabled = models.JSONField(default=dict, blank=True, verbose_name=_('Enabled Features'))

    # Security
    require_2fa = models.BooleanField(default=False, verbose_name=_('Require 2FA'))
    password_policy = models.JSONField(default=dict, blank=True, verbose_name=_('Password Policy'))
    session_timeout_minutes = models.PositiveIntegerField(default=30, verbose_name=_('Session Timeout'))

    # Notifications
    email_notifications = models.BooleanField(default=True, verbose_name=_('Email Notifications'))
    webhook_url = models.URLField(blank=True, verbose_name=_('Webhook URL'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Tenant Settings')
        verbose_name_plural = _('Tenant Settings')

    def __str__(self):
        return f"Settings for {self.tenant.name}"
