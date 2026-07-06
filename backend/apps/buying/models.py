from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.core.models import Company, Warehouse, Branch
from apps.inventory.models import Item

PAYMENT_TERMS = [
    ('Net 15', 'Net 15'), ('Net 30', 'Net 30'), ('Net 60', 'Net 60'),
    ('Due on Receipt', 'Due on Receipt'), ('Advance', 'Advance'),
]
PAYMENT_METHODS = [('Bank Transfer', 'Bank Transfer'), ('Cash', 'Cash'), ('Cheque', 'Cheque'), ('Credit Card', 'Credit Card')]


class Supplier(models.Model):
    STATUS_CHOICES = [('Active', 'Active'), ('Inactive', 'Inactive'), ('Blacklisted', 'Blacklisted')]
    SUPPLIER_TYPES = [('Company', 'Company'), ('Individual', 'Individual')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='suppliers')
    name = models.CharField(max_length=255)
    supplier_type = models.CharField(max_length=50, choices=SUPPLIER_TYPES, default='Company')
    contact_person = models.CharField(max_length=255, blank=True)
    tax_id = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Saudi Arabia')
    bank_account = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    iban = models.CharField(max_length=50, blank=True)
    payment_terms = models.CharField(max_length=50, choices=PAYMENT_TERMS, blank=True)
    credit_limit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='SAR')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Active')
    rating = models.PositiveSmallIntegerField(null=True, blank=True, choices=[(i, str(i)) for i in range(1, 6)])
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [('Draft', 'Draft'), ('Submitted', 'Submitted'), ('Received', 'Received'), ('Cancelled', 'Cancelled')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='purchase_orders')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchase_orders')
    po_number = models.CharField(max_length=100, unique=True)
    transaction_date = models.DateField()
    required_by = models.DateField(null=True, blank=True)
    terms = models.TextField(blank=True)
    total_qty = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Draft')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    currency = models.CharField(max_length=10, default='SAR')
    payment_terms = models.CharField(max_length=50, choices=PAYMENT_TERMS, blank=True)
    discount = models.DecimalField(max_digits=18, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    incoterm = models.CharField(max_length=50, blank=True, choices=[
        ('EXW', 'EXW'), ('FOB', 'FOB'), ('CIF', 'CIF'), ('DDP', 'DDP'), ('DAP', 'DAP'),
    ])
    approved_by = models.ForeignKey('hr.Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_purchase_orders')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_tax(self):
        return sum((t.tax_amount for t in self.tax_charges.all()), 0)

    @property
    def total_paid(self):
        return sum((p.amount for p in self.payments.all()), 0)

    @property
    def outstanding_amount(self):
        return self.grand_total - self.total_paid

    def recalculate_totals(self):
        """Recompute totals from line items and tax charges. Called
        automatically via signals whenever items/taxes change."""
        items = list(self.items.all())
        self.total_qty = sum((i.qty for i in items), 0)
        self.total_amount = sum((i.amount for i in items), 0)
        subtotal_after_discount = self.total_amount - (self.discount or 0)
        self.grand_total = subtotal_after_discount + self.total_tax
        PurchaseOrder.objects.filter(pk=self.pk).update(
            total_qty=self.total_qty, total_amount=self.total_amount, grand_total=self.grand_total
        )

    def receive_stock(self):
        """Called when the PO transitions to 'Received'. Creates a Receipt
        StockEntry for every line item and marks them fully received."""
        from apps.inventory.models import StockEntry
        if not self.warehouse:
            raise DjangoValidationError("Cannot mark a purchase order as Received without a warehouse set.")
        items = list(self.items.all())
        if not items:
            raise DjangoValidationError("Cannot receive a purchase order with no line items.")
        with transaction.atomic():
            for line in items:
                StockEntry.objects.create(
                    company=self.company, branch=self.branch, warehouse=self.warehouse,
                    item=line.item, entry_type='Receipt', quantity=line.qty, rate=line.rate,
                    reference=f"PO {self.po_number}",
                )
                line.received_qty = line.qty
                PurchaseOrderItem.objects.filter(pk=line.pk).update(received_qty=line.qty)

    def __str__(self):
        return self.po_number


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    qty = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0.01)])
    rate = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    amount = models.DecimalField(max_digits=18, decimal_places=2, editable=False, default=0)
    received_qty = models.DecimalField(max_digits=18, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    def save(self, *args, **kwargs):
        self.amount = self.qty * self.rate
        super().save(*args, **kwargs)


class PurchaseTaxCharge(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='tax_charges')
    description = models.CharField(max_length=255, default='VAT')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15, validators=[MinValueValidator(0)])
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    def __str__(self):
        return f"{self.description} ({self.tax_rate}%)"


class PurchasePayment(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0.01)])
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS, default='Bank Transfer')
    reference = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.purchase_order.po_number} - {self.amount}"
