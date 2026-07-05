from django.db import models
from apps.core.models import Company, Warehouse
from apps.inventory.models import Item

PAYMENT_TERMS = [
    ('Net 15', 'Net 15'), ('Net 30', 'Net 30'), ('Net 60', 'Net 60'),
    ('Due on Receipt', 'Due on Receipt'), ('Advance', 'Advance'),
]
PAYMENT_METHODS = [('Bank Transfer', 'Bank Transfer'), ('Cash', 'Cash'), ('Cheque', 'Cheque'), ('Credit Card', 'Credit Card')]


class Supplier(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='suppliers')
    name = models.CharField(max_length=255)
    tax_id = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
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
    currency = models.CharField(max_length=10, default='SAR')
    payment_terms = models.CharField(max_length=50, choices=PAYMENT_TERMS, blank=True)
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

    def __str__(self):
        return self.po_number


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    qty = models.DecimalField(max_digits=18, decimal_places=2)
    rate = models.DecimalField(max_digits=18, decimal_places=2)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    received_qty = models.DecimalField(max_digits=18, decimal_places=2, default=0)


class PurchaseTaxCharge(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='tax_charges')
    description = models.CharField(max_length=255, default='VAT')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15)
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.description} ({self.tax_rate}%)"


class PurchasePayment(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS, default='Bank Transfer')
    reference = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.purchase_order.po_number} - {self.amount}"
