"""SSO services: OIDC (OAuth2 Enterprise), SAML 2.0, LDAP/Active Directory.

All three resolve to the same contract: authenticate() -> user info dict,
then jit_provision() maps attributes and creates/updates the local user.
"""
import base64
import hashlib
import logging
import secrets
import urllib.parse

import requests
from django.contrib.auth import get_user_model

from .models import IdentityProvider

logger = logging.getLogger(__name__)


class OIDCService:
    """Authorization-code flow with PKCE against any OIDC-compliant IdP
    (Azure AD, Okta, Keycloak, Google Workspace...)."""

    def __init__(self, provider: IdentityProvider):
        self.p = provider
        self._config = None

    @property
    def config(self):
        if self._config is None:
            r = requests.get(
                f"{self.p.issuer.rstrip('/')}/.well-known/openid-configuration",
                timeout=10)
            r.raise_for_status()
            self._config = r.json()
        return self._config

    def authorization_url(self, redirect_uri: str, state: str) -> dict:
        verifier = secrets.token_urlsafe(64)
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
        params = {
            'response_type': 'code', 'client_id': self.p.client_id,
            'redirect_uri': redirect_uri, 'scope': self.p.scopes,
            'state': state, 'code_challenge': challenge,
            'code_challenge_method': 'S256',
        }
        return {
            'url': f"{self.config['authorization_endpoint']}?"
                   f"{urllib.parse.urlencode(params)}",
            'code_verifier': verifier,
        }

    def exchange_code(self, code: str, redirect_uri: str,
                      code_verifier: str) -> dict:
        r = requests.post(self.config['token_endpoint'], data={
            'grant_type': 'authorization_code', 'code': code,
            'redirect_uri': redirect_uri, 'client_id': self.p.client_id,
            'client_secret': self.p.client_secret,
            'code_verifier': code_verifier,
        }, timeout=10)
        r.raise_for_status()
        tokens = r.json()
        u = requests.get(self.config['userinfo_endpoint'], headers={
            'Authorization': f"Bearer {tokens['access_token']}"}, timeout=10)
        u.raise_for_status()
        return u.json()


class SAMLService:
    """SAML 2.0 SP metadata + assertion validation via python3-saml when
    installed; degrades to explicit error (never silent bypass)."""

    def __init__(self, provider: IdentityProvider):
        self.p = provider

    def settings_dict(self, sp_base_url: str) -> dict:
        return {
            'sp': {
                'entityId': f'{sp_base_url}/api/v1/iam/saml/metadata/',
                'assertionConsumerService': {
                    'url': f'{sp_base_url}/api/v1/iam/saml/acs/',
                    'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST'},
            },
            'idp': {
                'entityId': self.p.entity_id,
                'singleSignOnService': {
                    'url': self.p.sso_url,
                    'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'},
                'x509cert': self.p.x509_cert,
            },
        }

    def process_response(self, request_data: dict, sp_base_url: str) -> dict:
        try:
            from onelogin.saml2.auth import OneLogin_Saml2_Auth
        except ImportError as exc:
            raise RuntimeError(
                'python3-saml not installed - SAML login unavailable') from exc
        auth = OneLogin_Saml2_Auth(request_data,
                                   self.settings_dict(sp_base_url))
        auth.process_response()
        if auth.get_errors():
            raise PermissionError(f'SAML validation failed: {auth.get_errors()}')
        attrs = {k: v[0] if isinstance(v, list) and v else v
                 for k, v in (auth.get_attributes() or {}).items()}
        attrs.setdefault('email', auth.get_nameid())
        return attrs


class LDAPService:
    """LDAP / Active Directory bind-authentication."""

    def __init__(self, provider: IdentityProvider):
        self.p = provider

    def authenticate(self, username: str, password: str) -> dict:
        try:
            import ldap3
        except ImportError as exc:
            raise RuntimeError(
                'ldap3 not installed - LDAP/AD login unavailable') from exc
        server = ldap3.Server(self.p.ldap_server, get_info=ldap3.NONE)
        # search the user DN with the service account
        svc = ldap3.Connection(server, self.p.ldap_bind_dn,
                               self.p.ldap_bind_password, auto_bind=True)
        svc.search(self.p.ldap_user_search,
                   f'(|(sAMAccountName={username})(mail={username}))',
                   attributes=['mail', 'givenName', 'sn', 'memberOf'])
        if not svc.entries:
            raise PermissionError('User not found in directory')
        entry = svc.entries[0]
        user_dn = entry.entry_dn
        # bind AS the user to verify the password
        ldap3.Connection(server, user_dn, password, auto_bind=True)
        return {
            'email': str(entry.mail) if entry.mail else username,
            'first_name': str(entry.givenName or ''),
            'last_name': str(entry.sn or ''),
            'groups': [str(g) for g in (entry.memberOf or [])],
        }


def jit_provision(provider: IdentityProvider, attributes: dict):
    """Just-in-time provisioning: map IdP attributes -> local user."""
    User = get_user_model()
    amap = provider.attribute_map or {}
    email = attributes.get(amap.get('email', 'email'))
    if not email:
        raise PermissionError('IdP response is missing an email attribute')
    defaults = {
        'first_name': attributes.get(amap.get('first_name', 'first_name'), ''),
        'last_name': attributes.get(amap.get('last_name', 'last_name'), ''),
    }
    user = User.objects.filter(email=email).first()
    if user is None:
        if not provider.jit_provisioning:
            raise PermissionError(
                'User not provisioned and JIT provisioning is disabled')
        user = User.objects.create_user(email=email,
                                        password=None, **defaults)
        user.set_unusable_password()
        user.save()
        if provider.default_groups:
            from django.contrib.auth.models import Group
            for g in provider.default_groups:
                grp, _ = Group.objects.get_or_create(name=g)
                user.groups.add(grp)
        logger.info('JIT-provisioned %s via %s', email, provider.name)
    return user
