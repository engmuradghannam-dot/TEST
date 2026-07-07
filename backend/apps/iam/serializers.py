from rest_framework import serializers
from .models import (
    IdentityProvider, SSOConnection, SAMLRequestLog,
    RoleDefinition, RoleMiningJob, RoleMiningSuggestion, PermissionAnomaly,
    UserRoleAssignment, SeparationOfDutiesRule,
    PrivilegedAccount, PrivilegedSession, PasswordVault, VaultAccessLog,
    PrivilegedCommandPolicy, AuthenticationPolicy, UserDevice,
    SecurityEvent, AdaptiveAuthentication, LoginAttempt,
    ServiceAccount, APIKeyRotation, JITAccessRequest
)

class IdentityProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentityProvider
        fields = '__all__'
        extra_kwargs = {
            'saml_sp_private_key': {'write_only': True},
            'ldap_bind_password': {'write_only': True},
            'oauth_client_secret': {'write_only': True},
        }

class SSOConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SSOConnection
        fields = '__all__'
        extra_kwargs = {
            'access_token': {'write_only': True},
            'refresh_token': {'write_only': True},
            'id_token': {'write_only': True},
        }

class RoleDefinitionSerializer(serializers.ModelSerializer):
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = RoleDefinition
        fields = '__all__'

    def get_user_count(self, obj):
        return obj.assignments.filter(is_active=True).count()

class RoleMiningJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleMiningJob
        fields = '__all__'

class PermissionAnomalySerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = PermissionAnomaly
        fields = '__all__'

class PrivilegedAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivilegedAccount
        fields = '__all__'
        extra_kwargs = {
            'encrypted_password': {'write_only': True},
            'encrypted_private_key': {'write_only': True},
            'encrypted_api_key': {'write_only': True},
        }

class PrivilegedSessionSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = PrivilegedSession
        fields = '__all__'

class PasswordVaultSerializer(serializers.ModelSerializer):
    class Meta:
        model = PasswordVault
        fields = '__all__'
        extra_kwargs = {
            'encrypted_value': {'write_only': True},
        }

class AuthenticationPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthenticationPolicy
        fields = '__all__'

class SecurityEventSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = SecurityEvent
        fields = '__all__'

class ServiceAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceAccount
        fields = '__all__'
        extra_kwargs = {
            'client_secret_hash': {'write_only': True},
        }

class JITAccessRequestSerializer(serializers.ModelSerializer):
    requester_email = serializers.CharField(source='requester.email', read_only=True)
    requested_role_name = serializers.CharField(source='requested_role.name', read_only=True)

    class Meta:
        model = JITAccessRequest
        fields = '__all__'
