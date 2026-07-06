from django.db import models, transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.core.models import Company, Warehouse, Branch


class ItemGroup(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='item_groups')
    name = models.CharField(max_length=255)
    parent_group = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name


class Item(models.Model):
    ITEM_TYPES = [('Stock', 'Stock'), ('Service', 'Service'), ('Asset', 'Asset'), ('Bundle', 'Bundle')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='items')
    item_code = models.CharField(max_length=100, unique=True)
    item_name = models.CharField(max_length=255)
    item_type = models.CharField(max_length=50, choices=ITEM_TYPES, default='Stock')
    item_group = models.ForeignKey(ItemGroup, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    standard_rate = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    is_stock_item = models.BooleanField(default=True)
    is_purchase_item = models.BooleanField(default=True)
    is_sales_item = models.BooleanField(default=True)
    is_service_item = models.BooleanField(default=False)
    reorder_level = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    reorder_qty = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    uom = models.CharField(max_length=50, default='Unit')
    barcode = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    dimensions = models.CharField(max_length=100, blank=True, help_text='e.g. 30x20x10 cm')
    color = models.CharField(max_length=50, blank=True)
    size = models.CharField(max_length=50, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    supplier = models.ForeignKey('buying.Supplier', on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    lead_time_days = models.PositiveIntegerField(null=True, blank=True)
    tax_category = models.CharField(max_length=100, blank=True)
    valuation_method = models.CharField(max_length=50, default='FIFO', choices=[
        ('FIFO', 'FIFO'), ('LIFO', 'LIFO'), ('Moving Average', 'Moving Average'),
    ])
    image = models.ImageField(upload_to='item_images/', blank=True, null=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.item_name

    @property
    def stock_quantity(self):
        total = 0
        for entry in self.stockentry_set.all():
            if entry.entry_type == 'Receipt':
                total += entry.quantity
            elif entry.entry_type == 'Issue':
                total -= entry.quantity
        return total


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
    STATUS_CHOICES = [('Draft', 'Draft'), ('Submitted', 'Submitted'), ('Cancelled', 'Cancelled')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    source_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    target_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    entry_type = models.CharField(max_length=50, choices=ENTRY_TYPES)
    transaction_date = models.DateTimeField(auto_now_add=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=2)
    uom = models.CharField(max_length=50, default='Unit')
    rate = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    posting_date = models.DateField(auto_now_add=True)
    reference = models.CharField(max_length=255, blank=True)
    batch_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Submitted')
    created_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    @property
    def total_cost(self):
        return self.quantity * self.rate

    def __str__(self):
        return f"{self.entry_type} - {self.item.item_code}"


class StockReconciliation(models.Model):
    REASON_CHOICES = [
        ('Physical Count', 'Physical Count'), ('Damage', 'Damage'),
        ('Theft', 'Theft'), ('System Error', 'System Error'), ('Other', 'Other'),
    ]
    STATUS_CHOICES = [('Draft', 'Draft'), ('Submitted', 'Submitted'), ('Cancelled', 'Cancelled')]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stock_reconciliations')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    reconciliation_date = models.DateField()
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    reason = models.CharField(max_length=50, choices=REASON_CHOICES, default='Physical Count')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Draft')
    approved_by = models.ForeignKey('hr.Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_reconciliations')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_difference_value(self):
        return sum((i.total_difference_value for i in self.items.all()), 0)

    def apply_adjustments(self):
        """Called when the reconciliation transitions to 'Submitted'.
        Creates a Receipt/Issue StockEntry per line to bring actual system
        stock in line with the counted quantity."""
        lines = list(self.items.all())
        if not lines:
            raise DjangoValidationError("Cannot submit a stock reconciliation with no counted items.")
        with transaction.atomic():
            for line in lines:
                diff = line.difference
                if diff == 0:
                    continue
                StockEntry.objects.create(
                    company=self.company, branch=self.branch, warehouse=self.warehouse,
                    item=line.item, entry_type='Receipt' if diff > 0 else 'Issue',
                    quantity=abs(diff), rate=line.unit_cost,
                    reference=f"Stock Reconciliation SR-{self.id}",
                )

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
