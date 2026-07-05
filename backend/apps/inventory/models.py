from django.db import models
from apps.core.models import Company, Warehouse


class ItemGroup(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='item_groups')
    name = models.CharField(max_length=255)
    parent_group = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name


class Item(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='items')
    item_code = models.CharField(max_length=100, unique=True)
    item_name = models.CharField(max_length=255)
    item_group = models.ForeignKey(ItemGroup, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    standard_rate = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    is_stock_item = models.BooleanField(default=True)
    is_purchase_item = models.BooleanField(default=True)
    is_sales_item = models.BooleanField(default=True)
    reorder_level = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    reorder_qty = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    uom = models.CharField(max_length=50, default='Unit')
    barcode = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.item_name


class ItemSerialNumber(models.Model):
    STATUS_CHOICES = [('Available', 'Available'), ('Sold', 'Sold'), ('Reserved', 'Reserved'), ('Scrapped', 'Scrapped')]
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='serial_numbers')
    serial_no = models.CharField(max_length=100, unique=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Available')
    warranty_expiry = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.serial_no


class ItemBatch(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='batches')
    batch_no = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    expiry_date = models.DateField(null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('item', 'batch_no')

    def __str__(self):
        return f"{self.item.item_code} - {self.batch_no}"


class StockEntry(models.Model):
    ENTRY_TYPES = [('Receipt', 'Receipt'), ('Issue', 'Issue'), ('Transfer', 'Transfer')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    entry_type = models.CharField(max_length=50, choices=ENTRY_TYPES)
    quantity = models.DecimalField(max_digits=18, decimal_places=2)
    rate = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    posting_date = models.DateField(auto_now_add=True)
    reference = models.CharField(max_length=255, blank=True)
    batch_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.entry_type} - {self.item.item_code}"


class StockReconciliation(models.Model):
    REASON_CHOICES = [
        ('Physical Count', 'Physical Count'), ('Damage', 'Damage'),
        ('Theft', 'Theft'), ('System Error', 'System Error'), ('Other', 'Other'),
    ]
    STATUS_CHOICES = [('Draft', 'Draft'), ('Submitted', 'Submitted'), ('Cancelled', 'Cancelled')]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stock_reconciliations')
    reconciliation_date = models.DateField()
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    reason = models.CharField(max_length=50, choices=REASON_CHOICES, default='Physical Count')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Draft')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_difference_value(self):
        return sum((i.total_difference_value for i in self.items.all()), 0)

    def __str__(self):
        return f"SR-{self.id} - {self.warehouse}"


class StockReconciliationItem(models.Model):
    reconciliation = models.ForeignKey(StockReconciliation, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    system_quantity = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    actual_quantity = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    @property
    def difference(self):
        return self.actual_quantity - self.system_quantity

    @property
    def total_difference_value(self):
        return self.difference * self.unit_cost

    def __str__(self):
        return f"{self.item.item_code} ({self.difference})"
