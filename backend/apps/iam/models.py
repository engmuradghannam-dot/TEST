from django.conf import settings
"""
Nexus IAM - Identity & Access Management
Complete implementation with:
- SSO (Single Sign-On)
- SAML 2.0
- OAuth 2.0 / OIDC Enterprise
- Active Directory / LDAP
- Role Mining
- Privileged Access Management (PAM)
"""

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import URLValidator
from django.utils import timezone
import uuid
import json


# ============================================================================
# 1. IDENTITY PROVIDERS (SSO / SAML / OAuth / AD)
# ============================================================================

class IdentityProvider(models.Model):
    """External Identity Providers for SSO"""

    PROVIDER_TYPES = [
        ('saml', 'SAML 2.0'),
        ('oauth2', 'OAuth 2.0 / OIDC'),
        ('ldap', 'LDAP / Active Directory'),
        ('oidc', 'OpenID Connect'),
        ('google', 'Google Workspace'),
        ('azure_ad', 'Microsoft Azure AD'),
        ('okta', 'Okta'),
        ('auth0', 'Auth0'),
        ('keycloak', 'Keycloak'),
        ('onelogin', 'OneLogin'),
        ('custom', 'Custom Provider'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('testing', 'Testing'),
        ('error', 'Error'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    provider_type = models.CharField(max_length=50, choices=PROVIDER_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')

    # Organization mapping
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='identity_providers', null=True, blank=True)
    is_global = models.BooleanField(default=False, help_text='Available for all tenants')

    # SAML 2.0 Configuration
    saml_entity_id = models.CharField(max_length=500, blank=True, help_text='SP Entity ID')
    saml_acs_url = models.URLField(blank=True, help_text='Assertion Consumer Service URL')
    saml_idp_entity_id = models.CharField(max_length=500, blank=True, help_text='IdP Entity ID')
    saml_idp_sso_url = models.URLField(blank=True, help_text='IdP Single Sign-On URL')
    saml_idp_slo_url = models.URLField(blank=True, help_text='IdP Single Logout URL')
    saml_idp_certificate = models.TextField(blank=True, help_text='IdP X.509 Certificate (PEM)')
    saml_sp_private_key = models.TextField(blank=True, help_text='SP Private Key (PEM)')
    saml_sp_public_key = models.TextField(blank=True, help_text='SP Public Key / Certificate (PEM)')
    saml_name_id_format = models.CharField(max_length=100, default='urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress')
    saml_authn_context = models.CharField(max_length=255, default='urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport')
    saml_want_assertions_signed = models.BooleanField(default=True)
    saml_want_response_signed = models.BooleanField(default=True)
    saml_sign_authn_request = models.BooleanField(default=True)
    saml_sign_logout_request = models.BooleanField(default=True)
    saml_digest_algorithm = models.CharField(max_length=50, default='http://www.w3.org/2001/04/xmlenc#sha256')
    saml_signature_algorithm = models.CharField(max_length=50, default='http://www.w3.org/2001/04/xmldsig-more#rsa-sha256')

    # OAuth 2.0 / OIDC Configuration
    oauth_client_id = models.CharField(max_length=500, blank=True)
    oauth_client_secret = models.CharField(max_length=500, blank=True)
    oauth_authorization_endpoint = models.URLField(blank=True)
    oauth_token_endpoint = models.URLField(blank=True)
    oauth_userinfo_endpoint = models.URLField(blank=True)
    oauth_jwks_uri = models.URLField(blank=True)
    oauth_issuer = models.URLField(blank=True)
    oauth_scopes = models.JSONField(default=list, blank=True, help_text='Requested scopes')
    oauth_pkce_enabled = models.BooleanField(default=True)
    oauth_response_type = models.CharField(max_length=50, default='code')
    oauth_grant_type = models.CharField(max_length=50, default='authorization_code')

    # LDAP / Active Directory Configuration
    ldap_server_uri = models.CharField(max_length=500, blank=True, help_text='ldap://dc.company.com:389 or ldaps://dc.company.com:636')
    ldap_bind_dn = models.CharField(max_length=500, blank=True, help_text='CN=admin,DC=company,DC=com')
    ldap_bind_password = models.CharField(max_length=500, blank=True)
    ldap_base_dn = models.CharField(max_length=500, blank=True, help_text='DC=company,DC=com')
    ldap_user_search_filter = models.CharField(max_length=500, default='(sAMAccountName=%(user)s)')
    ldap_user_dn_template = models.CharField(max_length=500, blank=True)
    ldap_group_search_base = models.CharField(max_length=500, blank=True)
    ldap_group_search_filter = models.CharField(max_length=500, default='(objectClass=group)')
    ldap_user_attr_map = models.JSONField(default=dict, blank=True, help_text='{"first_name": "givenName", "last_name": "sn", "email": "mail"}')
    ldap_group_attr_map = models.JSONField(default=dict, blank=True)
    ldap_start_tls = models.BooleanField(default=True)
    ldap_require_cert = models.CharField(max_length=50, default='DEMAND', choices=[('NEVER', 'Never'), ('ALLOW', 'Allow'), ('TRY', 'Try'), ('DEMAND', 'Demand')])
    ldap_connection_timeout = models.PositiveIntegerField(default=30)
    ldap_page_size = models.PositiveIntegerField(default=1000)
    ldap_sync_interval_minutes = models.PositiveIntegerField(default=60)
    ldap_last_sync = models.DateTimeField(null=True, blank=True)

    # Attribute Mapping (Common)
    attribute_mapping = models.JSONField(default=dict, blank=True, help_text='Map IdP attributes to user fields')
    role_mapping = models.JSONField(default=dict, blank=True, help_text='Map IdP groups/roles to Nexus roles')

    # Advanced Settings
    allow_auto_provisioning = models.BooleanField(default=True, help_text='Auto-create users on first login')
    allow_auto_deactivation = models.BooleanField(default=False, help_text='Deactivate users when removed from IdP')
    force_sso_login = models.BooleanField(default=False, help_text='Disable local login, force SSO')
    mfa_required = models.BooleanField(default=False)
    session_duration_minutes = models.PositiveIntegerField(default=480)
    idle_timeout_minutes = models.PositiveIntegerField(default=30)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    class Meta:
        ordering = ['name']
        verbose_name = 'Identity Provider'
        verbose_name_plural = 'Identity Providers'

    def __str__(self):
        return f"{self.name} ({self.provider_type})"


class SSOConnection(models.Model):
    """User connections to external identity providers"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='sso_connections')
    provider = models.ForeignKey(IdentityProvider, on_delete=models.CASCADE, related_name='connections')

    # External Identity
    external_user_id = models.CharField(max_length=500, db_index=True)
    external_email = models.EmailField(blank=True)
    external_username = models.CharField(max_length=255, blank=True)
    external_attributes = models.JSONField(default=dict, blank=True)

    # Session Tokens
    access_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)
    id_token = models.TextField(blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['provider', 'external_user_id']
        indexes = [
            models.Index(fields=['user', 'provider']),
        ]


class SAMLRequestLog(models.Model):
    """Audit log for SAML requests/responses"""

    REQUEST_TYPES = [
        ('authn_request', 'Authentication Request'),
        ('authn_response', 'Authentication Response'),
        ('logout_request', 'Logout Request'),
        ('logout_response', 'Logout Response'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    provider = models.ForeignKey(IdentityProvider, on_delete=models.CASCADE, related_name='saml_logs')
    request_type = models.CharField(max_length=50, choices=REQUEST_TYPES)
    request_id = models.CharField(max_length=255, db_index=True)
    relay_state = models.CharField(max_length=500, blank=True)

    # Request/Response data
    saml_request_xml = models.TextField(blank=True)
    saml_response_xml = models.TextField(blank=True)
    decoded_assertion = models.JSONField(default=dict, blank=True)

    # Result
    is_success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    user = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)

    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


# ============================================================================
# 2. ROLE MINING & INTELLIGENT RBAC
# ============================================================================

class RoleDefinition(models.Model):
    """Granular role definitions with permissions"""

    ROLE_CATEGORIES = [
        ('system', 'System'),
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('operator', 'Operator'),
        ('viewer', 'Viewer'),
        ('custom', 'Custom'),
        ('privileged', 'Privileged'),
        ('service', 'Service Account'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=ROLE_CATEGORIES, default='custom')

    # Organization
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='roles', null=True, blank=True)
    is_system_role = models.BooleanField(default=False, help_text='Built-in system role')
    is_global = models.BooleanField(default=False)

    # Permissions (JSON for flexibility)
    permissions = models.JSONField(default=dict, help_text='{"module": {"action": true/false}}')

    # Data Scope
    data_scope = models.JSONField(default=dict, blank=True, help_text='{"branches": ["*"], "warehouses": ["*"], "departments": ["*"]}')

    # Time-based restrictions
    time_restrictions = models.JSONField(default=dict, blank=True, help_text='{"allowed_days": [1,2,3,4,5], "allowed_hours": {"start": "08:00", "end": "18:00"}}')

    # Approval workflow
    requires_approval = models.BooleanField(default=False)
    approver_roles = models.JSONField(default=list, blank=True)
    max_approval_duration_hours = models.PositiveIntegerField(default=48)

    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']
        unique_together = ['company', 'name']

    def __str__(self):
        return self.name


class RoleMiningJob(models.Model):
    """Automated role mining and analysis"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='role_mining_jobs')

    # Analysis Parameters
    analysis_type = models.CharField(max_length=50, choices=[
        ('permission_clustering', 'Permission Clustering'),
        ('usage_pattern', 'Usage Pattern Analysis'),
        ('access_similarity', 'Access Similarity'),
        ('anomaly_detection', 'Anomaly Detection'),
        ('role_optimization', 'Role Optimization'),
    ])

    # Data Source
    lookback_days = models.PositiveIntegerField(default=90)
    min_confidence = models.DecimalField(max_digits=5, decimal_places=2, default=80.00)

    # Results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    results = models.JSONField(default=dict, blank=True)
    suggested_roles = models.JSONField(default=list, blank=True)
    anomalies_found = models.JSONField(default=list, blank=True)

    # Statistics
    users_analyzed = models.PositiveIntegerField(default=0)
    permissions_analyzed = models.PositiveIntegerField(default=0)
    roles_suggested = models.PositiveIntegerField(default=0)
    anomalies_detected = models.PositiveIntegerField(default=0)

    # Execution
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class RoleMiningSuggestion(models.Model):
    """Individual role suggestions from mining"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    job = models.ForeignKey(RoleMiningJob, on_delete=models.CASCADE, related_name='suggestions')

    suggested_role_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2)

    # Analysis
    based_on_users = models.JSONField(default=list, help_text='User IDs this role is based on')
    common_permissions = models.JSONField(default=list)
    common_modules = models.JSONField(default=list)

    # Recommendation
    recommended_permissions = models.JSONField(default=dict)
    recommended_users = models.JSONField(default=list)

    # Status
    is_applied = models.BooleanField(default=False)
    applied_at = models.DateTimeField(null=True, blank=True)
    applied_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)
    feedback = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


class PermissionAnomaly(models.Model):
    """Detected permission anomalies"""

    SEVERITY_CHOICES = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    ANOMALY_TYPES = [
        ('excessive_permissions', 'Excessive Permissions'),
        ('dormant_access', 'Dormant Access'),
        ('privilege_escalation', 'Privilege Escalation'),
        ('separation_of_duties', 'SoD Violation'),
        ('orphaned_account', 'Orphaned Account'),
        ('shared_credentials', 'Shared Credentials'),
        ('after_hours_access', 'After Hours Access'),
        ('unusual_location', 'Unusual Location Access'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    job = models.ForeignKey(RoleMiningJob, on_delete=models.CASCADE, related_name='anomalies', null=True, blank=True)

    anomaly_type = models.CharField(max_length=50, choices=ANOMALY_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)

    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='permission_anomalies')
    description = models.TextField()
    details = models.JSONField(default=dict)

    # Risk scoring
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Remediation
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    resolution_notes = models.TextField(blank=True)
    auto_remediation_triggered = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-risk_score', '-created_at']


class UserRoleAssignment(models.Model):
    """User role assignments with temporal control"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='role_assignments')
    role = models.ForeignKey(RoleDefinition, on_delete=models.CASCADE, related_name='assignments')

    # Temporal control
    assigned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_temporary = models.BooleanField(default=False)
    temporary_reason = models.TextField(blank=True)

    # Approval
    approved_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_roles')
    approved_at = models.DateTimeField(null=True, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='revoked_roles')
    revocation_reason = models.TextField(blank=True)

    # Context
    branch_scope = models.JSONField(default=list, blank=True)
    department_scope = models.JSONField(default=list, blank=True)
    warehouse_scope = models.JSONField(default=list, blank=True)

    class Meta:
        unique_together = ['user', 'role']
        ordering = ['-assigned_at']


class SeparationOfDutiesRule(models.Model):
    """SoD (Segregation of Duties) rules"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='sod_rules')

    # Conflicting roles/permissions
    role_set_a = models.JSONField(default=list, help_text='Role IDs that conflict with role_set_b')
    role_set_b = models.JSONField(default=list)

    # Or permission-level conflicts
    permission_set_a = models.JSONField(default=list)
    permission_set_b = models.JSONField(default=list)

    # Enforcement
    is_enforced = models.BooleanField(default=True)
    allow_exception = models.BooleanField(default=False)
    exception_approvers = models.JSONField(default=list, blank=True)

    # Violations tracking
    violation_count = models.PositiveIntegerField(default=0)
    last_violation_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


# ============================================================================
# 3. PRIVILEGED ACCESS MANAGEMENT (PAM)
# ============================================================================

class PrivilegedAccount(models.Model):
    """Managed privileged accounts"""

    ACCOUNT_TYPES = [
        ('database_admin', 'Database Admin'),
        ('server_admin', 'Server Admin'),
        ('network_admin', 'Network Admin'),
        ('cloud_admin', 'Cloud Admin'),
        ('application_admin', 'Application Admin'),
        ('security_admin', 'Security Admin'),
        ('service_account', 'Service Account'),
        ('api_key', 'API Key'),
        ('ssh_key', 'SSH Key'),
        ('certificate', 'Certificate'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('rotating', 'Rotating'),
        ('compromised', 'Compromised'),
        ('pending_rotation', 'Pending Rotation'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPES)
    description = models.TextField(blank=True)

    # Organization
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='privileged_accounts')

    # Credentials (encrypted at rest)
    username = models.CharField(max_length=255, blank=True)
    encrypted_password = models.TextField(blank=True)
    encrypted_private_key = models.TextField(blank=True)
    encrypted_api_key = models.TextField(blank=True)
    certificate_data = models.TextField(blank=True)

    # Target system
    target_host = models.CharField(max_length=500, blank=True)
    target_port = models.PositiveIntegerField(null=True, blank=True)
    target_database = models.CharField(max_length=255, blank=True)
    target_service = models.CharField(max_length=255, blank=True)

    # Rotation settings
    auto_rotation_enabled = models.BooleanField(default=True)
    rotation_interval_days = models.PositiveIntegerField(default=90)
    last_rotated_at = models.DateTimeField(null=True, blank=True)
    next_rotation_due = models.DateTimeField(null=True, blank=True)
    rotation_history = models.JSONField(default=list, blank=True)

    # Checkout settings
    requires_checkout = models.BooleanField(default=True)
    max_checkout_duration_minutes = models.PositiveIntegerField(default=60)
    require_approval_for_checkout = models.BooleanField(default=True)
    approver_roles = models.JSONField(default=list, blank=True)

    # Session recording
    session_recording_enabled = models.BooleanField(default=True)
    command_logging_enabled = models.BooleanField(default=True)
    screen_recording_enabled = models.BooleanField(default=False)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    risk_level = models.CharField(max_length=20, default='high', choices=[('critical', 'Critical'), ('high', 'High'), ('medium', 'Medium'), ('low', 'Low')])

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    class Meta:
        ordering = ['-risk_level', 'name']


class PrivilegedSession(models.Model):
    """Checkout sessions for privileged accounts"""

    STATUS_CHOICES = [
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
        ('revoked', 'Revoked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    account = models.ForeignKey(PrivilegedAccount, on_delete=models.CASCADE, related_name='sessions')
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='privileged_sessions')

    # Request
    reason = models.TextField()
    requested_at = models.DateTimeField(auto_now_add=True)
    requested_duration_minutes = models.PositiveIntegerField(default=60)

    # Approval
    approved_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_sessions')
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)

    # Session
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_approval')
    started_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    ended_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='ended_sessions')

    # Credentials (temporary)
    temporary_password = models.TextField(blank=True)
    temporary_key = models.TextField(blank=True)

    # Session data
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    commands_executed = models.JSONField(default=list, blank=True)
    files_accessed = models.JSONField(default=list, blank=True)

    # Recording
    session_recording_url = models.URLField(blank=True)
    command_log = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-requested_at']


class PasswordVault(models.Model):
    """Enterprise password vault"""

    SECRET_TYPES = [
        ('password', 'Password'),
        ('api_key', 'API Key'),
        ('ssh_key', 'SSH Private Key'),
        ('database_url', 'Database URL'),
        ('oauth_token', 'OAuth Token'),
        ('certificate', 'Certificate'),
        ('license_key', 'License Key'),
        ('encryption_key', 'Encryption Key'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    secret_type = models.CharField(max_length=50, choices=SECRET_TYPES)
    description = models.TextField(blank=True)

    # Encrypted value
    encrypted_value = models.TextField()
    encrypted_value_v2 = models.TextField(blank=True, help_text='Re-encrypted with newer key')

    # Access control
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='vault_secrets')
    allowed_users = models.ManyToManyField('core.User', blank=True, related_name='accessible_secrets')
    allowed_roles = models.ManyToManyField(RoleDefinition, blank=True, related_name='accessible_secrets')

    # Usage tracking
    access_count = models.PositiveIntegerField(default=0)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    last_accessed_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    # Rotation
    auto_rotate = models.BooleanField(default=False)
    rotation_interval_days = models.PositiveIntegerField(default=90)
    last_rotated_at = models.DateTimeField(null=True, blank=True)
    next_rotation_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    tags = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    class Meta:
        ordering = ['name']


class VaultAccessLog(models.Model):
    """Audit log for vault access"""

    ACTION_TYPES = [
        ('view', 'View'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('rotate', 'Rotate'),
        ('checkout', 'Checkout'),
        ('checkin', 'Checkin'),
        ('copy', 'Copy'),
        ('export', 'Export'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    secret = models.ForeignKey(PasswordVault, on_delete=models.CASCADE, related_name='access_logs')
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='vault_access_logs')
    action = models.CharField(max_length=20, choices=ACTION_TYPES)

    success = models.BooleanField(default=True)
    failure_reason = models.TextField(blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class PrivilegedCommandPolicy(models.Model):
    """Command policies for privileged sessions"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='command_policies')

    # Command rules
    allowed_commands = models.JSONField(default=list, blank=True, help_text='Regex patterns for allowed commands')
    blocked_commands = models.JSONField(default=list, blank=True, help_text='Regex patterns for blocked commands')
    require_approval_commands = models.JSONField(default=list, blank=True)

    # Auto-actions
    block_sudo = models.BooleanField(default=False)
    block_rm_rf = models.BooleanField(default=True)
    block_drop_database = models.BooleanField(default=True)
    block_password_changes = models.BooleanField(default=True)

    # Alerting
    alert_on_violation = models.BooleanField(default=True)
    auto_terminate_on_violation = models.BooleanField(default=False)
    violation_threshold = models.PositiveIntegerField(default=3)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


# ============================================================================
# 4. ADVANCED AUTHENTICATION & SECURITY
# ============================================================================

class AuthenticationPolicy(models.Model):
    """Organization-wide authentication policies"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='auth_policies')
    is_default = models.BooleanField(default=False)

    # Password Policy
    min_password_length = models.PositiveIntegerField(default=12)
    require_uppercase = models.BooleanField(default=True)
    require_lowercase = models.BooleanField(default=True)
    require_numbers = models.BooleanField(default=True)
    require_special_chars = models.BooleanField(default=True)
    password_history_count = models.PositiveIntegerField(default=5)
    max_password_age_days = models.PositiveIntegerField(default=90)

    # MFA Policy
    mfa_required = models.BooleanField(default=False)
    mfa_methods = models.JSONField(default=list, blank=True, help_text='["totp", "sms", "email", "hardware_key", "biometric"]')
    mfa_enforcement_level = models.CharField(max_length=20, default='optional', choices=[('optional', 'Optional'), ('required', 'Required'), ('risk_based', 'Risk-Based')])

    # Session Policy
    session_timeout_minutes = models.PositiveIntegerField(default=480)
    idle_timeout_minutes = models.PositiveIntegerField(default=30)
    max_concurrent_sessions = models.PositiveIntegerField(default=3)
    allow_remember_me = models.BooleanField(default=True)
    remember_me_duration_days = models.PositiveIntegerField(default=30)

    # Lockout Policy
    max_failed_attempts = models.PositiveIntegerField(default=5)
    lockout_duration_minutes = models.PositiveIntegerField(default=30)
    progressive_lockout = models.BooleanField(default=True)

    # Risk-Based Authentication
    risk_based_auth_enabled = models.BooleanField(default=True)
    risk_factors = models.JSONField(default=dict, blank=True, help_text='{"new_device": true, "new_location": true, "unusual_time": true}')
    high_risk_action = models.CharField(max_length=50, default='mfa_challenge', choices=[('mfa_challenge', 'MFA Challenge'), ('block', 'Block'), ('admin_approval', 'Admin Approval')])

    # Device Policy
    device_trust_required = models.BooleanField(default=False)
    allowed_device_types = models.JSONField(default=list, blank=True)
    require_device_registration = models.BooleanField(default=True)

    # Location Policy
    geo_restriction_enabled = models.BooleanField(default=False)
    allowed_countries = models.JSONField(default=list, blank=True)
    blocked_countries = models.JSONField(default=list, blank=True)
    allowed_ip_ranges = models.JSONField(default=list, blank=True)
    blocked_ip_ranges = models.JSONField(default=list, blank=True)

    # Time Policy
    time_restriction_enabled = models.BooleanField(default=False)
    allowed_days = models.JSONField(default=list, blank=True)
    allowed_hours_start = models.TimeField(default='00:00')
    allowed_hours_end = models.TimeField(default='23:59')
    timezone = models.CharField(max_length=50, default='UTC')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class UserDevice(models.Model):
    """Registered user devices"""

    TRUST_STATUS = [
        ('trusted', 'Trusted'),
        ('untrusted', 'Untrusted'),
        ('pending', 'Pending'),
        ('blocked', 'Blocked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='devices')

    device_name = models.CharField(max_length=255, blank=True)
    device_type = models.CharField(max_length=50, choices=[('desktop', 'Desktop'), ('mobile', 'Mobile'), ('tablet', 'Tablet'), ('other', 'Other')])
    device_fingerprint = models.CharField(max_length=500, db_index=True)

    os_family = models.CharField(max_length=100, blank=True)
    os_version = models.CharField(max_length=100, blank=True)
    browser_family = models.CharField(max_length=100, blank=True)
    browser_version = models.CharField(max_length=100, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)

    trust_status = models.CharField(max_length=20, choices=TRUST_STATUS, default='pending')
    is_current = models.BooleanField(default=False)

    last_used_at = models.DateTimeField(null=True, blank=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_used_at']
        unique_together = ['user', 'device_fingerprint']


class SecurityEvent(models.Model):
    """Security event logging"""

    EVENT_CATEGORIES = [
        ('authentication', 'Authentication'),
        ('authorization', 'Authorization'),
        ('privilege', 'Privilege Access'),
        ('data_access', 'Data Access'),
        ('configuration', 'Configuration'),
        ('threat', 'Threat Detection'),
        ('compliance', 'Compliance'),
    ]

    SEVERITY_LEVELS = [
        ('info', 'Info'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    category = models.CharField(max_length=50, choices=EVENT_CATEGORIES)
    event_type = models.CharField(max_length=100)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)

    user = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='security_events')
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='security_events', null=True, blank=True)

    description = models.TextField()
    details = models.JSONField(default=dict, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=255, blank=True)

    # Alerting
    alert_triggered = models.BooleanField(default=False)
    alert_sent_to = models.JSONField(default=list, blank=True)

    # Response
    auto_response_taken = models.JSONField(default=dict, blank=True)
    requires_investigation = models.BooleanField(default=False)
    investigation_status = models.CharField(max_length=50, default='open', choices=[('open', 'Open'), ('investigating', 'Investigating'), ('resolved', 'Resolved'), ('false_positive', 'False Positive')])

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'severity', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['company', 'created_at']),
        ]


class AdaptiveAuthentication(models.Model):
    """Risk scoring and adaptive authentication"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='risk_scores')

    # Risk factors
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    risk_level = models.CharField(max_length=20, default='low', choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')])

    # Factor scores
    device_trust_score = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    location_risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    behavior_risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    time_risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    credential_risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    device_fingerprint = models.CharField(max_length=500, blank=True)

    # Decision
    decision = models.CharField(max_length=50, default='allow', choices=[('allow', 'Allow'), ('challenge', 'Challenge'), ('block', 'Block'), ('step_up', 'Step-Up MFA')])
    challenge_type = models.CharField(max_length=50, blank=True)

    # Session
    session_id = models.CharField(max_length=255, blank=True)
    login_attempt = models.ForeignKey('LoginAttempt', on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class LoginAttempt(models.Model):
    """Detailed login attempt tracking"""

    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('blocked', 'Blocked'),
        ('locked', 'Locked'),
        ('mfa_required', 'MFA Required'),
        ('mfa_failed', 'MFA Failed'),
        ('risk_blocked', 'Risk Blocked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='login_attempts', null=True, blank=True)
    email = models.EmailField(db_index=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    failure_reason = models.CharField(max_length=255, blank=True)

    # Auth method
    auth_method = models.CharField(max_length=50, default='password', choices=[('password', 'Password'), ('sso', 'SSO'), ('mfa', 'MFA'), ('api_key', 'API Key'), ('token', 'Token')])
    provider = models.ForeignKey(IdentityProvider, on_delete=models.SET_NULL, null=True, blank=True)

    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    user_agent = models.TextField(blank=True)
    device_fingerprint = models.CharField(max_length=500, blank=True)

    # MFA
    mfa_method = models.CharField(max_length=50, blank=True)
    mfa_success = models.BooleanField(null=True, blank=True)

    # Risk
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'status', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
        ]


# ============================================================================
# 5. API SECURITY & SERVICE ACCOUNTS
# ============================================================================

class ServiceAccount(models.Model):
    """Machine-to-machine service accounts"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='service_accounts')

    # Credentials
    client_id = models.CharField(max_length=255, unique=True)
    client_secret_hash = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255, unique=True, blank=True)

    # Permissions
    scopes = models.JSONField(default=list, blank=True)
    allowed_ips = models.JSONField(default=list, blank=True)
    allowed_origins = models.JSONField(default=list, blank=True)

    # Rate limiting
    rate_limit_requests_per_minute = models.PositiveIntegerField(default=1000)
    rate_limit_burst = models.PositiveIntegerField(default=100)

    # Usage
    total_requests = models.PositiveBigIntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['name']


class APIKeyRotation(models.Model):
    """API key rotation tracking"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    service_account = models.ForeignKey(ServiceAccount, on_delete=models.CASCADE, related_name='key_rotations')

    old_key_hash = models.CharField(max_length=255)
    new_key_hash = models.CharField(max_length=255)

    rotated_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)
    rotated_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)

    # Grace period
    old_key_expires_at = models.DateTimeField()
    old_key_revoked_at = models.DateTimeField(null=True, blank=True)


# ============================================================================
# 6. JUST-IN-TIME (JIT) ACCESS
# ============================================================================

class JITAccessRequest(models.Model):
    """Just-in-time privileged access requests"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
        ('expired', 'Expired'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('revoked', 'Revoked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    requester = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='jit_requests')

    # What is being requested
    requested_role = models.ForeignKey(RoleDefinition, on_delete=models.CASCADE, related_name='jit_requests')
    requested_account = models.ForeignKey(PrivilegedAccount, on_delete=models.CASCADE, related_name='jit_requests', null=True, blank=True)

    # Duration
    requested_duration_hours = models.PositiveIntegerField(default=4)
    actual_duration_hours = models.PositiveIntegerField(null=True, blank=True)

    # Reason
    reason = models.TextField()
    ticket_reference = models.CharField(max_length=255, blank=True)

    # Approval workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approvers = models.ManyToManyField('core.User', blank=True, related_name='jit_approvals')
    approval_chain = models.JSONField(default=list, blank=True)
    current_approval_step = models.PositiveIntegerField(default=0)

    # Time window
    requested_start_time = models.DateTimeField()
    requested_end_time = models.DateTimeField()
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)

    # Auto-revocation
    auto_revoke_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='revoked_jit')
    revocation_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class ElevationRequest(models.Model):
    """Lightweight user-level privilege elevation (ERP user roles,
    not server/infrastructure accounts). Simpler than JITAccessRequest."""
    STATUS = [('pending', 'Pending'), ('approved', 'Approved'),
              ('denied', 'Denied'), ('expired', 'Expired'), ('revoked', 'Revoked')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='elevation_requests')
    role_requested = models.CharField(max_length=100)
    justification = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name='approved_elevations')
    approved_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    requested_duration_hours = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['-requested_at']

    @property
    def is_currently_active(self):
        return (self.status == 'approved' and self.expires_at
                and timezone.now() < self.expires_at)
