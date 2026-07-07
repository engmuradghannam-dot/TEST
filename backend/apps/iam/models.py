"""Enterprise IAM models: SSO providers, privileged access, device trust."""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class IdentityProvider(models.Model):
    """SSO provider config: OIDC (OAuth2 Enterprise), SAML 2.0, LDAP/AD."""
    PROTOCOLS = [('oidc', 'OpenID Connect / OAuth2'),
                 ('saml', 'SAML 2.0'),
                 ('ldap', 'LDAP / Active Directory')]

    name = models.CharField(max_length=100, unique=True)
    protocol = models.CharField(max_length=10, choices=PROTOCOLS)
    is_active = models.BooleanField(default=True)
    # OIDC
    issuer = models.URLField(blank=True, help_text='OIDC issuer / discovery base')
    client_id = models.CharField(max_length=255, blank=True)
    client_secret = models.CharField(max_length=255, blank=True)
    scopes = models.CharField(max_length=255, default='openid email profile')
    # SAML
    entity_id = models.CharField(max_length=255, blank=True)
    sso_url = models.URLField(blank=True)
    x509_cert = models.TextField(blank=True)
    # LDAP / AD
    ldap_server = models.CharField(max_length=255, blank=True,
                                   help_text='ldaps://dc.example.com')
    ldap_bind_dn = models.CharField(max_length=255, blank=True)
    ldap_bind_password = models.CharField(max_length=255, blank=True)
    ldap_user_search = models.CharField(
        max_length=255, blank=True,
        help_text='e.g. OU=Users,DC=example,DC=com')
    # provisioning
    jit_provisioning = models.BooleanField(
        default=True, help_text='Create users on first SSO login')
    default_groups = models.JSONField(default=list, blank=True)
    attribute_map = models.JSONField(
        default=dict, blank=True,
        help_text='{"email": "mail", "first_name": "givenName"}')

    def __str__(self):
        return f"{self.name} ({self.protocol})"


class DeviceFingerprint(models.Model):
    """Known devices per user — a Zero-Trust signal."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, related_name='devices')
    fingerprint = models.CharField(max_length=64, db_index=True)
    user_agent = models.TextField(blank=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    is_trusted = models.BooleanField(default=False)
    trusted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [('user', 'fingerprint')]


class LoginContext(models.Model):
    """Historical login context — feeds behavioral baselines."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='login_contexts')
    ip_address = models.GenericIPAddressField()
    country = models.CharField(max_length=2, blank=True)
    device = models.ForeignKey(DeviceFingerprint, null=True, blank=True,
                               on_delete=models.SET_NULL)
    hour_of_day = models.PositiveSmallIntegerField()
    succeeded = models.BooleanField(default=True)
    trust_score = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


class PrivilegedSession(models.Model):
    """PAM: time-boxed privilege elevation with approval + full audit."""
    STATUS = [('requested', 'Requested'), ('approved', 'Approved'),
              ('denied', 'Denied'), ('active', 'Active'),
              ('expired', 'Expired'), ('revoked', 'Revoked')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='privileged_sessions')
    role_requested = models.CharField(
        max_length=100, help_text='e.g. billing_admin, db_operator')
    justification = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS,
                              default='requested')
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                    blank=True, on_delete=models.SET_NULL,
                                    related_name='approved_pam_sessions')
    starts_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    max_duration_minutes = models.PositiveIntegerField(default=60)
    actions_log = models.JSONField(default=list, blank=True)

    @property
    def is_currently_active(self):
        return (self.status == 'active' and self.expires_at
                and timezone.now() < self.expires_at)

    def approve(self, approver):
        if approver.pk == self.user_id:
            raise ValueError('Self-approval is not allowed')
        self.status = 'active'
        self.approved_by = approver
        self.starts_at = timezone.now()
        self.expires_at = self.starts_at + timezone.timedelta(
            minutes=self.max_duration_minutes)
        self.save()

    def revoke(self):
        self.status = 'revoked'
        self.expires_at = timezone.now()
        self.save(update_fields=['status', 'expires_at'])


class RoleMiningReport(models.Model):
    """Role Mining: clusters of co-occurring permissions -> suggested roles."""
    generated_at = models.DateTimeField(auto_now_add=True)
    suggestions = models.JSONField(default=list)
    users_analyzed = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-generated_at']
