
from rest_framework import serializers
from .models import Tenant, Domain, TenantUser, TenantMembership, TenantSettings


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant model."""
    user_count = serializers.IntegerField(source='memberships.filter(is_active=True).count', read_only=True)
    domain_count = serializers.IntegerField(source='domains.count', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)

    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'schema_name', 'status', 'plan', 'plan_name',
            'paid_until', 'on_trial', 'trial_end_date', 'max_users', 'max_storage_mb',
            'user_count', 'domain_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'schema_name', 'created_at', 'updated_at']


class DomainSerializer(serializers.ModelSerializer):
    """Serializer for Domain model."""
    class Meta:
        model = Domain
        fields = ['id', 'domain', 'is_primary', 'domain_type', 'ssl_enabled', 'created_at']
        read_only_fields = ['id', 'created_at']


class TenantMembershipSerializer(serializers.ModelSerializer):
    """Serializer for TenantMembership model."""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)

    class Meta:
        model = TenantMembership
        fields = ['id', 'user', 'user_email', 'user_name', 'tenant', 'tenant_name', 
                  'role', 'permissions', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class TenantUserSerializer(serializers.ModelSerializer):
    """Serializer for TenantUser model."""
    memberships = TenantMembershipSerializer(many=True, read_only=True)

    class Meta:
        model = TenantUser
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'phone',
            'avatar', 'is_active', 'is_verified', 'two_factor_enabled',
            'language', 'timezone', 'memberships', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = TenantUser(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user


class TenantSettingsSerializer(serializers.ModelSerializer):
    """Serializer for TenantSettings model."""
    class Meta:
        model = TenantSettings
        fields = [
            'id', 'tenant', 'company_name', 'company_logo', 'favicon',
            'primary_color', 'features_enabled', 'require_2fa',
            'password_policy', 'session_timeout_minutes',
            'email_notifications', 'webhook_url'
        ]
        read_only_fields = ['id', 'tenant']


class TenantCreateSerializer(serializers.Serializer):
    """Serializer for creating a new tenant."""
    name = serializers.CharField(max_length=100)
    slug = serializers.SlugField(max_length=63)
    owner_email = serializers.EmailField()
    owner_password = serializers.CharField(write_only=True, min_length=8)
    owner_first_name = serializers.CharField(max_length=150)
    owner_last_name = serializers.CharField(max_length=150)
    plan_id = serializers.UUIDField(required=False)

    def validate_slug(self, value):
        if Tenant.objects.filter(slug=value).exists():
            raise serializers.ValidationError("This slug is already taken.")
        return value
