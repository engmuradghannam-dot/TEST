from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    IdentityProviderViewSet, RoleDefinitionViewSet,
    RoleMiningJobViewSet, PermissionAnomalyViewSet,
    PrivilegedAccountViewSet, PrivilegedSessionViewSet,
    PasswordVaultViewSet, SecurityEventViewSet,
    ServiceAccountViewSet, JITAccessRequestViewSet,
    SAMLAuthView, SAMLACSView, OAuthCallbackView, LDAPSyncView
)

router = DefaultRouter()
router.register(r'identity-providers', IdentityProviderViewSet, basename='identity-provider')
router.register(r'roles', RoleDefinitionViewSet, basename='role-definition')
router.register(r'role-mining', RoleMiningJobViewSet, basename='role-mining')
router.register(r'anomalies', PermissionAnomalyViewSet, basename='permission-anomaly')
router.register(r'privileged-accounts', PrivilegedAccountViewSet, basename='privileged-account')
router.register(r'privileged-sessions', PrivilegedSessionViewSet, basename='privileged-session')
router.register(r'vault', PasswordVaultViewSet, basename='password-vault')
router.register(r'security-events', SecurityEventViewSet, basename='security-event')
router.register(r'service-accounts', ServiceAccountViewSet, basename='service-account')
router.register(r'jit-access', JITAccessRequestViewSet, basename='jit-access')

urlpatterns = [
    path('', include(router.urls)),
    path('sso/saml/initiate/', SAMLAuthView.as_view(), name='saml-initiate'),
    path('sso/saml/acs/', SAMLACSView.as_view(), name='saml-acs'),
    path('sso/oauth/callback/', OAuthCallbackView.as_view(), name='oauth-callback'),
    path('sso/ldap/sync/', LDAPSyncView.as_view(), name='ldap-sync'),
]
