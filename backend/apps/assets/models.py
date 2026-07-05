from django.db import models
from apps.core.models import Company
from apps.hr.models import Employee

DEPRECIATION_METHODS = [
    ('Straight Line', 'Straight Line'),
    ('Declining Balance', 'Declining Balance'),
    ('None', 'None'),
]


class AssetCategory(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='asset_categories')
    name = models.CharField(max_length=255)
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

class Asset(models.Model):
    STATUS_CHOICES = [('Draft', 'Draft'), ('Submitted', 'Submitted'), ('In Maintenance', 'In Maintenance'), ('Disposed', 'Disposed')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='assets')
    asset_name = models.CharField(max_length=255)
    asset_code = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(AssetCategory, on_delete=models.SET_NULL, null=True, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    purchase_value = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    current_value = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    salvage_value = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    depreciation_method = models.CharField(max_length=50, choices=DEPRECIATION_METHODS, default='Straight Line')
    depreciation_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='Annual depreciation rate as a percentage')
    useful_life_years = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Draft')
    custodian = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.asset_name

    @property
    def accumulated_depreciation(self):
        import datetime
        from decimal import Decimal
        if self.depreciation_method == 'None' or not self.purchase_date or not self.depreciation_rate:
            return Decimal('0')
        years_elapsed = Decimal((datetime.date.today() - self.purchase_date).days) / Decimal('365.25')
        depreciable_base = self.purchase_value - self.salvage_value
        if self.depreciation_method == 'Straight Line':
            annual_depreciation = depreciable_base * (self.depreciation_rate / Decimal('100'))
            return min(annual_depreciation * years_elapsed, depreciable_base)
        if self.depreciation_method == 'Declining Balance':
            remaining = self.purchase_value
            for _ in range(int(years_elapsed)):
                remaining -= remaining * (self.depreciation_rate / Decimal('100'))
            return max(self.purchase_value - remaining, Decimal('0'))
        return Decimal('0')

    @property
    def book_value(self):
        return self.purchase_value - self.accumulated_depreciation
