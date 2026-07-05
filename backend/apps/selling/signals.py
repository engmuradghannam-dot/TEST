from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import SalesOrderItem, SalesTaxCharge, SalesOrder


def _recalc(sales_order_id):
    if not sales_order_id:
        return
    try:
        so = SalesOrder.objects.get(pk=sales_order_id)
    except SalesOrder.DoesNotExist:
        return
    so.recalculate_totals()


@receiver(post_save, sender=SalesOrderItem)
@receiver(post_delete, sender=SalesOrderItem)
def sync_so_totals_on_item_change(sender, instance, **kwargs):
    _recalc(instance.sales_order_id)


@receiver(post_save, sender=SalesTaxCharge)
@receiver(post_delete, sender=SalesTaxCharge)
def sync_so_totals_on_tax_change(sender, instance, **kwargs):
    _recalc(instance.sales_order_id)
