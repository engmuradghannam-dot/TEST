from rest_framework import serializers
from .models import Account, JournalEntry, JournalEntryLine, CostCenter, Budget

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'

class JournalEntryLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalEntryLine
        fields = '__all__'

class JournalEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalEntry
        fields = '__all__'

class CostCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostCenter
        fields = '__all__'

class BudgetSerializer(serializers.ModelSerializer):
    variance = serializers.ReadOnlyField()
    variance_percentage = serializers.ReadOnlyField()
    class Meta:
        model = Budget
        fields = '__all__'
