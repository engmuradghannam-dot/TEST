from rest_framework import serializers
from .models import User, Company, Branch, Warehouse, PrintTemplate

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'role', 'company', 'is_active', 'date_joined']

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = '__all__'

class PrintTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintTemplate
        fields = '__all__'
