"""Fiscal layer: fiscal years/periods, currencies & exchange rates,
tax rules, and financial closing.

Completes the accounting core:
- FiscalYear / FiscalPeriod  -> posting-date control + period locking
- Currency / ExchangeRate    -> multi-currency engine (base per company)
- TaxRule                    -> per-country/per-category tax engine
- FiscalYear.close()         -> year-end closing entry (P&L -> Retained Earnings)
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from apps.core.models import Company


class FiscalYear(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE,
                                related_name='fiscal_years')
    name = models.CharField(max_length=50)            # e.g. "FY2026"
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)
    closing_entry = models.ForeignKey('accounts.JournalEntry', null=True,
                                      blank=True, on_delete=models.SET_NULL,
                                      related_name='+')

    class Meta:
        unique_together = [('company', 'name')]
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({self.company_id})"

    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("start_date must be before end_date")
        overlap = FiscalYear.objects.filter(
            company=self.company,
            start_date__lte=self.end_date,
            end_date__gte=self.start_date,
        ).exclude(pk=self.pk)
        if overlap.exists():
            raise ValidationError("Fiscal year overlaps an existing one")

    def generate_periods(self, frequency: str = 'monthly'):
        """Create posting periods covering the year (monthly default)."""
        import calendar
        from datetime import date
        periods = []
        cur = self.start_date
        idx = 1
        while cur <= self.end_date:
            last_day = calendar.monthrange(cur.year, cur.month)[1]
            end = min(date(cur.year, cur.month, last_day), self.end_date)
            periods.append(FiscalPeriod(
                fiscal_year=self, number=idx,
                name=cur.strftime('%b %Y'),
                start_date=cur, end_date=end,
            ))
            idx += 1
            cur = end + timezone.timedelta(days=1)
        FiscalPeriod.objects.bulk_create(periods)
        return periods

    @transaction.atomic
    def close(self, retained_earnings_account, user=None):
        """Year-end closing: net all income/expense balances into
        retained earnings via a single closing journal entry, then lock."""
        from apps.accounts.models import Account, JournalEntry, JournalEntryLine

        if self.is_closed:
            raise ValidationError("Fiscal year already closed")
        open_periods = self.periods.filter(is_locked=False).count()

        pl_accounts = Account.objects.filter(
            company=self.company, is_group=False,
            account_type__in=['Income', 'Expense'],
        ).exclude(balance=0)

        entry = JournalEntry.objects.create(
            company=self.company,
            entry_number=f"CLOSE-{self.name}-{self.company_id}",
            posting_date=self.end_date,
            journal_type='Journal Entry',
            description=f"Year-end closing {self.name}",
            posted_by=user, status='Draft',
        )
        net = Decimal('0')
        for acc in pl_accounts:
            bal = acc.balance
            # income accounts carry credit balances (negative in debit-normal
            # convention); expenses carry debit balances
            if acc.account_type == 'Income':
                JournalEntryLine.objects.create(
                    journal_entry=entry, account=acc,
                    debit=abs(bal), credit=0,
                    description='Close income to retained earnings')
                net += abs(bal)
            else:
                JournalEntryLine.objects.create(
                    journal_entry=entry, account=acc,
                    debit=0, credit=abs(bal),
                    description='Close expense to retained earnings')
                net -= abs(bal)
        JournalEntryLine.objects.create(
            journal_entry=entry, account=retained_earnings_account,
            debit=0 if net >= 0 else abs(net),
            credit=net if net >= 0 else 0,
            description='Net result to retained earnings')

        entry.total_debit = sum(l.debit for l in entry.lines.all())
        entry.total_credit = sum(l.credit for l in entry.lines.all())
        entry.status = 'Submitted'
        entry.save()
        entry.post_to_ledger()

        self.periods.update(is_locked=True)
        self.is_closed = True
        self.closed_at = timezone.now()
        self.closing_entry = entry
        self.save(update_fields=['is_closed', 'closed_at', 'closing_entry'])
        return entry


class FiscalPeriod(models.Model):
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE,
                                    related_name='periods')
    number = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    is_locked = models.BooleanField(default=False)

    class Meta:
        unique_together = [('fiscal_year', 'number')]
        ordering = ['fiscal_year', 'number']

    def __str__(self):
        return f"{self.fiscal_year.name}/{self.name}"

    @classmethod
    def for_date(cls, company, posting_date):
        return cls.objects.filter(
            fiscal_year__company=company,
            start_date__lte=posting_date, end_date__gte=posting_date,
        ).first()

    @classmethod
    def validate_posting(cls, company, posting_date):
        """Raise if the posting date falls in a locked/closed/missing period."""
        period = cls.for_date(company, posting_date)
        if period is None:
            raise ValidationError(
                f"No open fiscal period covers {posting_date}. "
                "Create the fiscal year first.")
        if period.is_locked or period.fiscal_year.is_closed:
            raise ValidationError(
                f"Fiscal period {period} is locked — posting rejected.")
        return period


class Currency(models.Model):
    code = models.CharField(max_length=3, primary_key=True)   # ISO 4217
    name = models.CharField(max_length=60)
    name_ar = models.CharField(max_length=60, blank=True)
    symbol = models.CharField(max_length=8, blank=True)
    decimals = models.PositiveSmallIntegerField(default=2)

    class Meta:
        verbose_name_plural = 'currencies'

    def __str__(self):
        return self.code


class ExchangeRate(models.Model):
    from_currency = models.ForeignKey(Currency, on_delete=models.CASCADE,
                                      related_name='rates_from')
    to_currency = models.ForeignKey(Currency, on_delete=models.CASCADE,
                                    related_name='rates_to')
    rate = models.DecimalField(max_digits=18, decimal_places=8)
    date = models.DateField(default=timezone.localdate)

    class Meta:
        unique_together = [('from_currency', 'to_currency', 'date')]
        ordering = ['-date']

    @classmethod
    def convert(cls, amount: Decimal, from_code: str, to_code: str,
                on_date=None) -> Decimal:
        if from_code == to_code:
            return Decimal(amount)
        on_date = on_date or timezone.localdate()
        rate = cls.objects.filter(
            from_currency_id=from_code, to_currency_id=to_code,
            date__lte=on_date).order_by('-date').first()
        if rate:
            return (Decimal(amount) * rate.rate).quantize(Decimal('0.01'))
        inverse = cls.objects.filter(
            from_currency_id=to_code, to_currency_id=from_code,
            date__lte=on_date).order_by('-date').first()
        if inverse and inverse.rate:
            return (Decimal(amount) / inverse.rate).quantize(Decimal('0.01'))
        raise ValidationError(
            f"No exchange rate {from_code}->{to_code} on or before {on_date}")


class TaxRule(models.Model):
    """Country-aware tax engine rule.

    Resolution order: (country, category) > (country, None) — most
    specific rule wins. Seeded defaults include SA VAT 15%."""
    TAX_TYPES = [('vat', 'VAT'), ('withholding', 'Withholding'),
                 ('excise', 'Excise'), ('zero', 'Zero-rated'),
                 ('exempt', 'Exempt')]

    company = models.ForeignKey(Company, on_delete=models.CASCADE,
                                null=True, blank=True, related_name='tax_rules',
                                help_text='Null = global default rule')
    country = models.CharField(max_length=2, default='SA')   # ISO 3166-1
    tax_type = models.CharField(max_length=15, choices=TAX_TYPES, default='vat')
    category = models.CharField(max_length=60, blank=True,
                                help_text='Item/service category; blank = all')
    rate = models.DecimalField(max_digits=6, decimal_places=3)
    account = models.ForeignKey('accounts.Account', null=True, blank=True,
                                on_delete=models.SET_NULL,
                                help_text='GL account for this tax')
    valid_from = models.DateField(default=timezone.localdate)
    valid_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['country', 'category']

    def __str__(self):
        return f"{self.country} {self.tax_type} {self.rate}%"

    @classmethod
    def resolve(cls, country: str, category: str = '', company=None,
                on_date=None, tax_type: str = 'vat'):
        on_date = on_date or timezone.localdate()
        base = cls.objects.filter(
            country=country, tax_type=tax_type, is_active=True,
            valid_from__lte=on_date,
        ).filter(models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=on_date))
        for scope in ([company] if company else []) + [None]:
            for cat in ([category] if category else []) + ['']:
                rule = base.filter(company=scope, category=cat).first()
                if rule:
                    return rule
        return None

    @classmethod
    def compute(cls, amount: Decimal, country: str = 'SA', **kwargs) -> dict:
        rule = cls.resolve(country, **kwargs)
        if rule is None or rule.tax_type in ('zero', 'exempt'):
            return {'rate': Decimal('0'), 'tax': Decimal('0'),
                    'total': Decimal(amount), 'rule': rule}
        tax = (Decimal(amount) * rule.rate / 100).quantize(Decimal('0.01'))
        return {'rate': rule.rate, 'tax': tax,
                'total': Decimal(amount) + tax, 'rule': rule}
