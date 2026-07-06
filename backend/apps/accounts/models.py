from django.db import models
from apps.core.models import Company

class Account(models.Model):
    ACCOUNT_TYPES = [
        ('Asset', 'Asset'), ('Liability', 'Liability'), ('Equity', 'Equity'),
        ('Income', 'Income'), ('Expense', 'Expense')
    ]
    ROOT_TYPES = [
        ('Asset', 'Asset'), ('Liability', 'Liability'), ('Equity', 'Equity'),
        ('Income', 'Income'), ('Expense', 'Expense')
    ]
    # Standard accounting convention: Asset/Expense accounts increase with a
    # Debit; Liability/Equity/Income accounts increase with a Credit.
    DEBIT_INCREASES = {'Asset', 'Expense'}

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='accounts')
    account_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPES)
    root_type = models.CharField(max_length=50, choices=ROOT_TYPES, blank=True)
    parent_account = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_group = models.BooleanField(default=False, help_text='Group accounts are headers that contain child accounts and cannot hold transactions directly.')
    is_bank_account = models.BooleanField(default=False)
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='SAR')
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    def post(self, debit_amount=0, credit_amount=0):
        """Apply a debit/credit to this account's running balance,
        respecting normal accounting sign convention based on root_type."""
        effective_type = self.root_type or self.account_type
        net = (debit_amount or 0) - (credit_amount or 0)
        if effective_type not in self.DEBIT_INCREASES:
            net = -net
        Account.objects.filter(pk=self.pk).update(balance=models.F('balance') + net)
        self.refresh_from_db(fields=['balance'])

    def __str__(self):
        return f"{self.account_number} - {self.account_name}"

class JournalEntry(models.Model):
    JOURNAL_TYPES = [
        ('Journal Entry', 'Journal Entry'), ('Bank Entry', 'Bank Entry'),
        ('Cash Entry', 'Cash Entry'), ('Credit Note', 'Credit Note'), ('Debit Note', 'Debit Note'),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='journal_entries')
    entry_number = models.CharField(max_length=100, unique=True)
    posting_date = models.DateField()
    reference = models.CharField(max_length=255, blank=True)
    journal_type = models.CharField(max_length=50, choices=JOURNAL_TYPES, default='Journal Entry')
    debit_account = models.ForeignKey(
        'Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='debit_journal_entries',
        help_text='Quick-entry shortcut for simple two-line postings. Complex postings use JournalEntryLine.'
    )
    credit_account = models.ForeignKey(
        'Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='credit_journal_entries'
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='SAR')
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1, help_text='Rate to convert `currency` into the company base currency')
    project = models.ForeignKey('projects.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='journal_entries')
    cost_center = models.ForeignKey('CostCenter', on_delete=models.SET_NULL, null=True, blank=True, related_name='journal_entries')
    total_debit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_credit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    branch = models.ForeignKey('core.Branch', on_delete=models.SET_NULL, null=True, blank=True)
    posted_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='posted_journal_entries')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=50, default='Draft', choices=[('Draft', 'Draft'), ('Submitted', 'Submitted')])
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def post_to_ledger(self):
        """Applies this entry's amounts to the real account balances.
        Called exactly once, when the entry transitions to 'Submitted'
        (see JournalEntrySerializer.update). Supports both the simple
        two-account shortcut and full multi-line postings.
        Rejects postings into locked/closed fiscal periods."""
        from django.core.exceptions import ValidationError as DjangoValidationError
        from apps.accounts.fiscal import FiscalPeriod

        # fiscal-period gate (only when a fiscal calendar exists)
        if FiscalPeriod.objects.filter(fiscal_year__company=self.company).exists():
            FiscalPeriod.validate_posting(self.company, self.posting_date)

        # double-entry integrity for multi-line postings
        line_qs = self.lines.all()
        if line_qs.exists():
            td = sum(l.debit for l in line_qs)
            tc = sum(l.credit for l in line_qs)
            if td != tc:
                raise DjangoValidationError(
                    f"Unbalanced entry: debits {td} != credits {tc}")

        lines = list(self.lines.all())
        if lines:
            for line in lines:
                if line.account.is_group:
                    raise DjangoValidationError(
                        f"Cannot post to '{line.account}': it is a group account (header), not a postable account."
                    )
            for line in lines:
                line.account.post(debit_amount=line.debit, credit_amount=line.credit)
        elif self.debit_account and self.credit_account:
            if self.debit_account.is_group or self.credit_account.is_group:
                raise DjangoValidationError("Cannot post to a group account (header) — choose a postable leaf account.")
            self.debit_account.post(debit_amount=self.amount)
            self.credit_account.post(credit_amount=self.amount)

    def __str__(self):
        return self.entry_number

class JournalEntryLine(models.Model):
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    description = models.TextField(blank=True)


class CostCenter(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='cost_centers')
    name = models.CharField(max_length=255)
    parent_cost_center = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Budget(models.Model):
    STATUS_CHOICES = [('Draft', 'Draft'), ('Active', 'Active'), ('Closed', 'Closed')]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='budgets')
    name = models.CharField(max_length=255)
    fiscal_year = models.CharField(max_length=20)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='budgets')
    budget_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    actual_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Draft')
    start_date = models.DateField()
    end_date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def variance(self):
        return self.actual_amount - self.budget_amount

    @property
    def variance_percentage(self):
        if not self.budget_amount:
            return 0
        return (self.variance / self.budget_amount) * 100

    def __str__(self):
        return f"{self.name} ({self.fiscal_year})"


# Fiscal layer models (fiscal years/periods, currency, tax engine)
from apps.accounts.fiscal import (  # noqa: E402,F401
    FiscalYear, FiscalPeriod, Currency, ExchangeRate, TaxRule,
)
