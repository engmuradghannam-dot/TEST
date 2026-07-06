from rest_framework import serializers
from .models import User, Company, Branch, Warehouse, PrintTemplate, Module, AuditLog

class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = '__all__'

class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True, default=None)
    class Meta:
        model = AuditLog
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'role', 'company', 'branch',
                  'two_factor_enabled', 'language', 'accessible_modules', 'user_permissions',
                  'is_active', 'is_staff', 'is_superuser', 'last_login', 'date_joined']

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'

class WarehouseSerializer(serializers.ModelSerializer):
    current_stock = serializers.ReadOnlyField()
    class Meta:
        model = Warehouse
        fields = '__all__'

class PrintTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintTemplate
        fields = '__all__'


class UIScreenSerializer(serializers.ModelSerializer):
    class Meta:
        from apps.core.models import UIScreen
        model = UIScreen
        fields = '__all__'
        read_only_fields = ('company', 'created_by')
