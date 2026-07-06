from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.core.models import Company, Warehouse, Branch
from apps.inventory.models import Item
from apps.buying.models import PAYMENT_TERMS, PAYMENT_METHODS


class Customer(models.Model):
    STATUS_CHOICES = [('Active', 'Active'), ('Inactive', 'Inactive'), ('Blacklisted', 'Blacklisted')]
    CUSTOMER_TYPES = [('Company', 'Company'), ('Individual', 'Individual')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='customers')
    name = models.CharField(max_length=255)
    customer_type = models.CharField(max_length=50, choices=CUSTOMER_TYPES, default='Company')
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


class SalesOrder(models.Model):
    STATUS_CHOICES = [('Draft', 'Draft'), ('Submitted', 'Submitted'), ('Delivered', 'Delivered'), ('Cancelled', 'Cancelled')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sales_orders')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='sales_orders')
    so_number = models.CharField(max_length=100, unique=True)
    transaction_date = models.DateField()
    delivery_date = models.DateField(null=True, blank=True)
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
    sales_person = models.ForeignKey('hr.Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_orders_handled')
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
        items = list(self.items.all())
        self.total_qty = sum((i.qty for i in items), 0)
        self.total_amount = sum((i.amount for i in items), 0)
        subtotal_after_discount = self.total_amount - (self.discount or 0)
        self.grand_total = subtotal_after_discount + self.total_tax
        SalesOrder.objects.filter(pk=self.pk).update(
            total_qty=self.total_qty, total_amount=self.total_amount, grand_total=self.grand_total
        )

    def deliver_stock(self):
        """Called when the SO transitions to 'Delivered'. Validates enough
        stock exists for every line BEFORE issuing anything (all-or-nothing),
        then creates an Issue StockEntry per line."""
        from apps.inventory.models import StockEntry
        if not self.warehouse:
            raise DjangoValidationError("Cannot mark a sales order as Delivered without a warehouse set.")
        items = list(self.items.all())
        if not items:
            raise DjangoValidationError("Cannot deliver a sales order with no line items.")
        shortages = []
        for line in items:
            available = line.item.stock_quantity
            if available < line.qty:
                shortages.append(f"{line.item.item_code} (available {available}, need {line.qty})")
        if shortages:
            raise DjangoValidationError(f"Insufficient stock to deliver: {', '.join(shortages)}")
        with transaction.atomic():
            for line in items:
                StockEntry.objects.create(
                    company=self.company, branch=self.branch, warehouse=self.warehouse,
                    item=line.item, entry_type='Issue', quantity=line.qty, rate=line.rate,
                    reference=f"SO {self.so_number}",
                )
                SalesOrderItem.objects.filter(pk=line.pk).update(delivered_qty=line.qty)

    def __str__(self):
        return self.so_number


class SalesOrderItem(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    qty = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0.01)])
    rate = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    amount = models.DecimalField(max_digits=18, decimal_places=2, editable=False, default=0)
    delivered_qty = models.DecimalField(max_digits=18, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    def save(self, *args, **kwargs):
        self.amount = self.qty * self.rate
        super().save(*args, **kwargs)


class SalesTaxCharge(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='tax_charges')
    description = models.CharField(max_length=255, default='VAT')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15, validators=[MinValueValidator(0)])
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    def __str__(self):
        return f"{self.description} ({self.tax_rate}%)"


class SalesPayment(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0.01)])
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS, default='Bank Transfer')
    reference = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sales_order.so_number} - {self.amount}"
