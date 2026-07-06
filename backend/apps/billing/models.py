
"""
Billing & Subscriptions with Stripe integration.
Plans, invoices, payments, and subscription management.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
import uuid


class Plan(models.Model):
    """
    Subscription plan model.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Plan details
    name = models.CharField(max_length=100, unique=True, verbose_name=_('Name'))
    slug = models.SlugField(max_length=100, unique=True, verbose_name=_('Slug'))
    description = models.TextField(blank=True, verbose_name=_('Description'))

    # Pricing
    class BillingInterval(models.TextChoices):
        MONTHLY = 'monthly', _('Monthly')
        QUARTERLY = 'quarterly', _('Quarterly')
        YEARLY = 'yearly', _('Yearly')
        LIFETIME = 'lifetime', _('Lifetime')

    interval = models.CharField(
        max_length=20,
        choices=BillingInterval.choices,
        default=BillingInterval.MONTHLY,
        verbose_name=_('Billing Interval')
    )

    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)],
        verbose_name=_('Price')
    )
    currency = models.CharField(max_length=3, default='USD', verbose_name=_('Currency'))

    # Stripe integration
    stripe_product_id = models.CharField(max_length=100, blank=True, verbose_name=_('Stripe Product ID'))
    stripe_price_id = models.CharField(max_length=100, blank=True, verbose_name=_('Stripe Price ID'))

    # Features & Limits
    features = models.JSONField(default=list, blank=True, verbose_name=_('Features'))
    max_users = models.PositiveIntegerField(default=5, verbose_name=_('Max Users'))
    max_storage_mb = models.PositiveIntegerField(default=100, verbose_name=_('Max Storage (MB)'))
    max_projects = models.PositiveIntegerField(default=10, verbose_name=_('Max Projects'))
    api_calls_per_month = models.PositiveIntegerField(default=10000, verbose_name=_('API Calls/Month'))

    # Plan type
    class PlanType(models.TextChoices):
        FREE = 'free', _('Free')
        STARTER = 'starter', _('Starter')
        PROFESSIONAL = 'professional', _('Professional')
        ENTERPRISE = 'enterprise', _('Enterprise')
        CUSTOM = 'custom', _('Custom')

    plan_type = models.CharField(
        max_length=20,
        choices=PlanType.choices,
        default=PlanType.STARTER,
        verbose_name=_('Plan Type')
    )

    # Status
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))
    is_public = models.BooleanField(default=True, verbose_name=_('Is Public'))
    sort_order = models.PositiveIntegerField(default=0, verbose_name=_('Sort Order'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        ordering = ['sort_order', 'price']
        verbose_name = _('Plan')
        verbose_name_plural = _('Plans')

    def __str__(self):
        return f"{self.name} (${self.price}/{self.interval})"

    def get_stripe_price_id(self):
        """Get or create Stripe price ID."""
        if not self.stripe_price_id:
            from .stripe_client import create_stripe_price
            self.stripe_price_id = create_stripe_price(self)
            self.save()
        return self.stripe_price_id


class Subscription(models.Model):
    """
    Tenant subscription model.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='subscription',
        verbose_name=_('Tenant')
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name=_('Plan')
    )

    # Stripe integration
    stripe_subscription_id = models.CharField(max_length=100, blank=True, verbose_name=_('Stripe Subscription ID'))
    stripe_customer_id = models.CharField(max_length=100, blank=True, verbose_name=_('Stripe Customer ID'))

    # Status
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        TRIALING = 'trialing', _('Trialing')
        PAST_DUE = 'past_due', _('Past Due')
        CANCELLED = 'cancelled', _('Cancelled')
        UNPAID = 'unpaid', _('Unpaid')
        PAUSED = 'paused', _('Paused')

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TRIALING,
        verbose_name=_('Status')
    )

    # Dates
    current_period_start = models.DateTimeField(null=True, blank=True, verbose_name=_('Current Period Start'))
    current_period_end = models.DateTimeField(null=True, blank=True, verbose_name=_('Current Period End'))
    trial_start = models.DateTimeField(null=True, blank=True, verbose_name=_('Trial Start'))
    trial_end = models.DateTimeField(null=True, blank=True, verbose_name=_('Trial End'))
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Cancelled At'))

    # Metadata
    cancel_at_period_end = models.BooleanField(default=False, verbose_name=_('Cancel at Period End'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Subscription')
        verbose_name_plural = _('Subscriptions')

    def __str__(self):
        return f"{self.tenant.name} - {self.plan.name} ({self.status})"

    def is_active(self):
        return self.status in [self.Status.ACTIVE, self.Status.TRIALING]

    def is_trialing(self):
        return self.status == self.Status.TRIALING

    def cancel(self):
        """Cancel subscription at period end."""
        self.cancel_at_period_end = True
        self.save()

        # Update Stripe subscription
        if self.stripe_subscription_id:
            from .stripe_client import cancel_stripe_subscription
            cancel_stripe_subscription(self.stripe_subscription_id)

    def reactivate(self):
        """Reactivate a cancelled subscription."""
        self.cancel_at_period_end = False
        self.status = self.Status.ACTIVE
        self.save()

        if self.stripe_subscription_id:
            from .stripe_client import reactivate_stripe_subscription
            reactivate_stripe_subscription(self.stripe_subscription_id)


class Invoice(models.Model):
    """
    Invoice model for billing records.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name=_('Tenant')
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        verbose_name=_('Subscription')
    )

    # Invoice details
    invoice_number = models.CharField(max_length=50, unique=True, verbose_name=_('Invoice Number'))

    # Stripe integration
    stripe_invoice_id = models.CharField(max_length=100, blank=True, verbose_name=_('Stripe Invoice ID'))
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True, verbose_name=_('Stripe Payment Intent ID'))

    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Subtotal'))
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name=_('Tax'))
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name=_('Discount'))
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Total'))
    currency = models.CharField(max_length=3, default='USD', verbose_name=_('Currency'))

    # Status
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        OPEN = 'open', _('Open')
        PAID = 'paid', _('Paid')
        UNCOLLECTIBLE = 'uncollectible', _('Uncollectible')
        VOID = 'void', _('Void')

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_('Status')
    )

    # Dates
    invoice_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Invoice Date'))
    due_date = models.DateTimeField(null=True, blank=True, verbose_name=_('Due Date'))
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Paid At'))

    # Line items
    line_items = models.JSONField(default=list, verbose_name=_('Line Items'))

    # PDF
    pdf_url = models.URLField(blank=True, verbose_name=_('PDF URL'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')

    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.tenant.name}"

    def calculate_total(self):
        """Calculate total from subtotal, tax, and discount."""
        self.total = self.subtotal + self.tax - self.discount
        self.save()

    def mark_as_paid(self):
        """Mark invoice as paid."""
        from django.utils import timezone
        self.status = self.Status.PAID
        self.paid_at = timezone.now()
        self.save()


class Payment(models.Model):
    """
    Payment record for tracking all payments.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('Tenant')
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name=_('Invoice')
    )

    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Amount'))
    currency = models.CharField(max_length=3, default='USD', verbose_name=_('Currency'))

    # Stripe
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True, verbose_name=_('Stripe Payment Intent'))
    stripe_charge_id = models.CharField(max_length=100, blank=True, verbose_name=_('Stripe Charge ID'))

    # Status
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PROCESSING = 'processing', _('Processing')
        SUCCEEDED = 'succeeded', _('Succeeded')
        FAILED = 'failed', _('Failed')
        REFUNDED = 'refunded', _('Refunded')
        PARTIALLY_REFUNDED = 'partially_refunded', _('Partially Refunded')

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_('Status')
    )

    # Payment method
    class PaymentMethod(models.TextChoices):
        CARD = 'card', _('Credit Card')
        BANK_TRANSFER = 'bank_transfer', _('Bank Transfer')
        PAYPAL = 'paypal', _('PayPal')
        APPLE_PAY = 'apple_pay', _('Apple Pay')
        GOOGLE_PAY = 'google_pay', _('Google Pay')

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CARD,
        verbose_name=_('Payment Method')
    )

    # Card details (last 4 only, for display)
    card_last4 = models.CharField(max_length=4, blank=True, verbose_name=_('Card Last 4'))
    card_brand = models.CharField(max_length=50, blank=True, verbose_name=_('Card Brand'))

    # Metadata
    description = models.TextField(blank=True, verbose_name=_('Description'))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_('Metadata'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')

    def __str__(self):
        return f"Payment {self.id} - ${self.amount} ({self.status})"


class UsageRecord(models.Model):
    """
    Track resource usage for billing and limits.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='usage_records',
        verbose_name=_('Tenant')
    )

    # Usage type
    class UsageType(models.TextChoices):
        API_CALL = 'api_call', _('API Call')
        STORAGE = 'storage', _('Storage (MB)')
        BANDWIDTH = 'bandwidth', _('Bandwidth (MB)')
        USER = 'user', _('User')
        PROJECT = 'project', _('Project')
        PLUGIN = 'plugin', _('Plugin')

    usage_type = models.CharField(
        max_length=20,
        choices=UsageType.choices,
        verbose_name=_('Usage Type')
    )

    quantity = models.DecimalField(max_digits=15, decimal_places=2, verbose_name=_('Quantity'))
    unit = models.CharField(max_length=50, verbose_name=_('Unit'))

    # Billing period
    billing_period_start = models.DateTimeField(verbose_name=_('Billing Period Start'))
    billing_period_end = models.DateTimeField(verbose_name=_('Billing Period End'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Usage Record')
        verbose_name_plural = _('Usage Records')

    def __str__(self):
        return f"{self.tenant.name} - {self.usage_type}: {self.quantity} {self.unit}"
