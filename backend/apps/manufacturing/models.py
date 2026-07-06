from django.db import models, transaction
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.core.models import Company, Warehouse, Branch
from apps.inventory.models import Item, StockEntry


class BOM(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='boms')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='boms')
    bom_name = models.CharField(max_length=255)
    version = models.CharField(max_length=50, default='1.0')
    quantity = models.DecimalField(max_digits=18, decimal_places=2, default=1)
    uom = models.CharField(max_length=50, default='Unit')
    operating_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    labor_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def raw_materials_cost(self):
        return sum((i.qty * i.rate for i in self.items.all()), 0)

    @property
    def total_cost(self):
        return self.raw_materials_cost + self.operating_cost + self.labor_cost

    def __str__(self):
        return self.bom_name


class BOMItem(models.Model):
    bom = models.ForeignKey(BOM, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    qty = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    uom = models.CharField(max_length=50, default='Unit')
    rate = models.DecimalField(max_digits=18, decimal_places=2, default=0)


class WorkOrder(models.Model):
    STATUS_CHOICES = [('Draft', 'Draft'), ('In Progress', 'In Progress'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')]
    PRIORITY_CHOICES = [('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High'), ('Urgent', 'Urgent')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='work_orders')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    bom = models.ForeignKey(BOM, on_delete=models.SET_NULL, null=True, blank=True)
    wo_number = models.CharField(max_length=100, unique=True)
    order_date = models.DateField(auto_now_add=True)
    item_to_manufacture = models.ForeignKey(Item, on_delete=models.CASCADE)
    qty_to_produce = models.DecimalField(max_digits=18, decimal_places=2)
    produced_qty = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    uom = models.CharField(max_length=50, default='Unit')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Draft')
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='Medium')
    workstation = models.CharField(max_length=255, blank=True)
    supervisor = models.ForeignKey('hr.Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_work_orders')
    planned_start = models.DateField(null=True, blank=True)
    planned_end = models.DateField(null=True, blank=True)
    actual_start = models.DateField(null=True, blank=True)
    actual_end = models.DateField(null=True, blank=True)
    estimated_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    actual_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def complete_production(self):
        """Called when the WorkOrder transitions to 'Completed'. Validates
        raw-material availability for the full BOM FIRST (all-or-nothing),
        then issues raw materials and receipts the finished good."""
        if not self.bom:
            raise DjangoValidationError("Cannot complete a work order without a BOM.")
        if not self.warehouse:
            raise DjangoValidationError("Cannot complete a work order without a warehouse.")
        bom_items = list(self.bom.items.all())
        if not bom_items:
            raise DjangoValidationError("The linked BOM has no raw materials defined.")

        shortages = []
        requirements = []
        for bom_item in bom_items:
            required = bom_item.qty * self.qty_to_produce
            available = bom_item.item.stock_quantity
            requirements.append((bom_item, required))
            if available < required:
                shortages.append(f"{bom_item.item.item_code} (available {available}, need {required})")
        if shortages:
            raise DjangoValidationError(f"Insufficient raw materials to complete production: {', '.join(shortages)}")

        with transaction.atomic():
            for bom_item, required in requirements:
                StockEntry.objects.create(
                    company=self.company, branch=self.branch, warehouse=self.warehouse,
                    item=bom_item.item, entry_type='Issue', quantity=required, rate=bom_item.rate,
                    reference=f"WO {self.wo_number} consumption",
                )
            StockEntry.objects.create(
                company=self.company, branch=self.branch, warehouse=self.warehouse,
                item=self.item_to_manufacture, entry_type='Receipt', quantity=self.qty_to_produce,
                rate=(self.actual_cost / self.qty_to_produce) if self.qty_to_produce else 0,
                reference=f"WO {self.wo_number} production",
            )
            WorkOrder.objects.filter(pk=self.pk).update(produced_qty=self.qty_to_produce)

    def __str__(self):
        return self.wo_number
