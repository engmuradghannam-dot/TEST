from rest_framework import serializers
from apps.core.workflow import validate_transition
from .models import Account, JournalEntry, JournalEntryLine, CostCenter, Budget

JOURNAL_TRANSITIONS = {
    'Draft': {'Submitted'},
    'Submitted': set(),
}

BUDGET_TRANSITIONS = {
    'Draft': {'Active', 'Closed'},
    'Active': {'Closed'},
    'Closed': set(),
}

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

    def validate(self, data):
        debit_account = data.get('debit_account', getattr(self.instance, 'debit_account', None))
        credit_account = data.get('credit_account', getattr(self.instance, 'credit_account', None))
        amount = data.get('amount', getattr(self.instance, 'amount', None))
        status = data.get('status', getattr(self.instance, 'status', 'Draft'))

        if debit_account and credit_account and debit_account == credit_account:
            raise serializers.ValidationError("Debit and credit accounts must be different.")

        if status == 'Submitted':
            total_debit = data.get('total_debit', getattr(self.instance, 'total_debit', 0)) or 0
            total_credit = data.get('total_credit', getattr(self.instance, 'total_credit', 0)) or 0
            uses_lines = self.instance and self.instance.lines.exists()
            if uses_lines:
                if total_debit != total_credit:
                    raise serializers.ValidationError(
                        f"Cannot submit an unbalanced journal entry: total debit ({total_debit}) "
                        f"!= total credit ({total_credit})."
                    )
            elif not amount or amount <= 0:
                raise serializers.ValidationError("Amount must be greater than zero to submit this entry.")

        if self.instance and status and status != self.instance.status:
            validate_transition(JOURNAL_TRANSITIONS, self.instance.status, status)
        return data

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

    def validate(self, data):
        start = data.get('start_date', getattr(self.instance, 'start_date', None))
        end = data.get('end_date', getattr(self.instance, 'end_date', None))
        if start and end and end < start:
            raise serializers.ValidationError("End date cannot be before start date.")

        new_status = data.get('status')
        if self.instance and new_status and new_status != self.instance.status:
            validate_transition(BUDGET_TRANSITIONS, self.instance.status, new_status)
        return data
