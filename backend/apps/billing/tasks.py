"""
Celery tasks for billing app.
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_payment(self, payment_id):
    """Process a payment asynchronously."""
    from .models import Payment
    try:
        payment = Payment.objects.get(id=payment_id)
        # Process payment logic
        payment.status = Payment.Status.SUCCEEDED
        payment.save()
        logger.info(f"Payment {payment_id} processed successfully")
    except Exception as exc:
        logger.error(f"Payment {payment_id} failed: {exc}")
        raise self.retry(exc=exc, countdown=60)

@shared_task
def check_expired_subscriptions():
    """Check and handle expired subscriptions."""
    from django.utils import timezone
    from .models import Subscription
    expired = Subscription.objects.filter(
        current_period_end__lt=timezone.now(),
        status=Subscription.Status.ACTIVE
    )
    for sub in expired:
        if sub.cancel_at_period_end:
            sub.status = Subscription.Status.CANCELLED
        else:
            sub.status = Subscription.Status.PAST_DUE
        sub.save()
        logger.info(f"Subscription {sub.id} marked as expired")

@shared_task
def generate_monthly_invoices():
    """Generate invoices for active subscriptions."""
    from .models import Subscription, Invoice
    from django.utils import timezone
    import calendar

    active_subs = Subscription.objects.filter(
        status__in=[Subscription.Status.ACTIVE, Subscription.Status.TRIALING]
    )

    for sub in active_subs:
        today = timezone.now()
        last_day = calendar.monthrange(today.year, today.month)[1]

        invoice = Invoice.objects.create(
            tenant=sub.tenant,
            subscription=sub,
            invoice_number=f"INV-{today.year}-{today.month:02d}-{sub.id}",
            subtotal=sub.plan.price,
            tax=0,
            discount=0,
            total=sub.plan.price,
            currency=sub.plan.currency,
            status=Invoice.Status.OPEN,
            due_date=today.replace(day=last_day),
            line_items=[{
                'description': f'{sub.plan.name} - {sub.plan.interval}',
                'quantity': 1,
                'unit_price': float(sub.plan.price),
                'total': float(sub.plan.price),
            }]
        )
        logger.info(f"Invoice {invoice.invoice_number} generated for {sub.tenant.name}")
