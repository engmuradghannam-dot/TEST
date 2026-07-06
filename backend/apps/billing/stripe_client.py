
"""
Stripe client for billing operations.
"""
import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import logging

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
if not stripe.api_key:
    logger.warning("STRIPE_SECRET_KEY not configured")


def create_stripe_customer(tenant, user):
    """Create a Stripe customer for a tenant."""
    try:
        customer = stripe.Customer.create(
            email=user.email,
            name=tenant.name,
            metadata={
                'tenant_id': str(tenant.id),
                'tenant_slug': tenant.slug,
            }
        )
        return customer.id
    except stripe.error.StripeError as e:
        logger.error(f"Stripe customer creation failed: {e}")
        raise


def create_stripe_price(plan):
    """Create a Stripe price for a plan."""
    try:
        # Create product if not exists
        if not plan.stripe_product_id:
            product = stripe.Product.create(
                name=plan.name,
                description=plan.description,
                metadata={'plan_id': str(plan.id)}
            )
            plan.stripe_product_id = product.id

        # Create price
        interval_map = {
            'monthly': 'month',
            'quarterly': 'month',
            'yearly': 'year',
            'lifetime': 'month',
        }

        price_data = {
            'unit_amount': int(plan.price * 100),  # Convert to cents
            'currency': plan.currency.lower(),
            'product': plan.stripe_product_id,
            'recurring': {
                'interval': interval_map.get(plan.interval, 'month'),
            } if plan.interval != 'lifetime' else None,
        }

        price = stripe.Price.create(**{k: v for k, v in price_data.items() if v is not None})
        return price.id
    except stripe.error.StripeError as e:
        logger.error(f"Stripe price creation failed: {e}")
        raise


def create_stripe_subscription(stripe_customer_id, stripe_price_id, trial_days=14):
    """Create a Stripe subscription."""
    try:
        subscription = stripe.Subscription.create(
            customer=stripe_customer_id,
            items=[{'price': stripe_price_id}],
            trial_period_days=trial_days,
            payment_behavior='default_incomplete',
            expand=['latest_invoice.payment_intent'],
        )
        return subscription
    except stripe.error.StripeError as e:
        logger.error(f"Stripe subscription creation failed: {e}")
        raise


def cancel_stripe_subscription(stripe_subscription_id):
    """Cancel a Stripe subscription at period end."""
    try:
        stripe.Subscription.modify(
            stripe_subscription_id,
            cancel_at_period_end=True
        )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe subscription cancellation failed: {e}")
        raise


def reactivate_stripe_subscription(stripe_subscription_id):
    """Reactivate a Stripe subscription."""
    try:
        stripe.Subscription.modify(
            stripe_subscription_id,
            cancel_at_period_end=False
        )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe subscription reactivation failed: {e}")
        raise


def create_stripe_payment_intent(amount, currency, customer_id, metadata=None):
    """Create a Stripe payment intent."""
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),
            currency=currency.lower(),
            customer=customer_id,
            metadata=metadata or {},
            automatic_payment_methods={'enabled': True},
        )
        return intent
    except stripe.error.StripeError as e:
        logger.error(f"Stripe payment intent creation failed: {e}")
        raise


def handle_stripe_webhook(payload, sig_header, webhook_secret):
    """Handle Stripe webhook events."""
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )

        if event['type'] == 'invoice.payment_succeeded':
            handle_payment_succeeded(event['data']['object'])
        elif event['type'] == 'invoice.payment_failed':
            handle_payment_failed(event['data']['object'])
        elif event['type'] == 'customer.subscription.deleted':
            handle_subscription_cancelled(event['data']['object'])
        elif event['type'] == 'customer.subscription.updated':
            handle_subscription_updated(event['data']['object'])

        return event
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Stripe webhook signature verification failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Stripe webhook handling failed: {e}")
        raise


def handle_payment_succeeded(invoice):
    """Handle successful payment."""
    from .models import Invoice, Payment
    from apps.tenants.models import Tenant

    try:
        tenant = Tenant.objects.get(
            subscription__stripe_customer_id=invoice['customer']
        )

        # Create or update invoice
        db_invoice, created = Invoice.objects.get_or_create(
            stripe_invoice_id=invoice['id'],
            defaults={
                'tenant': tenant,
                'invoice_number': invoice['number'],
                'subtotal': invoice['subtotal'] / 100,
                'tax': invoice.get('tax', 0) / 100,
                'total': invoice['total'] / 100,
                'currency': invoice['currency'].upper(),
                'status': Invoice.Status.PAID,
                'line_items': invoice.get('lines', {}).get('data', []),
            }
        )

        if not created:
            db_invoice.status = Invoice.Status.PAID
            db_invoice.paid_at = __import__('django.utils.timezone').now()
            db_invoice.save()

        # Create payment record
        Payment.objects.create(
            tenant=tenant,
            invoice=db_invoice,
            amount=invoice['total'] / 100,
            currency=invoice['currency'].upper(),
            status=Payment.Status.SUCCEEDED,
            stripe_payment_intent_id=invoice.get('payment_intent'),
            stripe_charge_id=invoice.get('charge'),
            payment_method=Payment.PaymentMethod.CARD,
            description=f"Payment for invoice {invoice['number']}"
        )

    except Tenant.DoesNotExist:
        logger.error(f"Tenant not found for Stripe customer: {invoice['customer']}")
    except Exception as e:
        logger.error(f"Payment success handling failed: {e}")


def handle_payment_failed(invoice):
    """Handle failed payment."""
    from .models import Invoice, Subscription

    try:
        db_invoice = Invoice.objects.get(stripe_invoice_id=invoice['id'])
        db_invoice.status = Invoice.Status.OPEN
        db_invoice.save()

        # Update subscription status
        subscription = Subscription.objects.get(
            stripe_subscription_id=invoice['subscription']
        )
        subscription.status = Subscription.Status.PAST_DUE
        subscription.save()

    except Invoice.DoesNotExist:
        logger.error(f"Invoice not found: {invoice['id']}")
    except Exception as e:
        logger.error(f"Payment failure handling failed: {e}")


def handle_subscription_cancelled(subscription):
    """Handle subscription cancellation."""
    from .models import Subscription

    try:
        sub = Subscription.objects.get(
            stripe_subscription_id=subscription['id']
        )
        sub.status = Subscription.Status.CANCELLED
        sub.cancelled_at = __import__('django.utils.timezone').now()
        sub.save()

        # Update tenant status
        sub.tenant.status = sub.tenant.Status.CANCELLED
        sub.tenant.save()

    except Subscription.DoesNotExist:
        logger.error(f"Subscription not found: {subscription['id']}")


def handle_subscription_updated(subscription):
    """Handle subscription update."""
    from .models import Subscription

    try:
        sub = Subscription.objects.get(
            stripe_subscription_id=subscription['id']
        )

        status_map = {
            'active': Subscription.Status.ACTIVE,
            'trialing': Subscription.Status.TRIALING,
            'past_due': Subscription.Status.PAST_DUE,
            'cancelled': Subscription.Status.CANCELLED,
            'unpaid': Subscription.Status.UNPAID,
            'paused': Subscription.Status.PAUSED,
        }

        sub.status = status_map.get(subscription['status'], Subscription.Status.ACTIVE)
        sub.current_period_start = __import__('datetime').datetime.fromtimestamp(
            subscription['current_period_start']
        )
        sub.current_period_end = __import__('datetime').datetime.fromtimestamp(
            subscription['current_period_end']
        )
        sub.cancel_at_period_end = subscription['cancel_at_period_end']
        sub.save()

    except Subscription.DoesNotExist:
        logger.error(f"Subscription not found: {subscription['id']}")
