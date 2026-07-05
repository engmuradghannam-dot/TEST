from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import PurchaseOrderItem, PurchaseTaxCharge, PurchaseOrder


def _recalc(purchase_order_id):
    if not purchase_order_id:
        return
    try:
        po = PurchaseOrder.objects.get(pk=purchase_order_id)
    except PurchaseOrder.DoesNotExist:
        return
    po.recalculate_totals()


@receiver(post_save, sender=PurchaseOrderItem)
@receiver(post_delete, sender=PurchaseOrderItem)
def sync_po_totals_on_item_change(sender, instance, **kwargs):
    _recalc(instance.purchase_order_id)


@receiver(post_save, sender=PurchaseTaxCharge)
@receiver(post_delete, sender=PurchaseTaxCharge)
def sync_po_totals_on_tax_change(sender, instance, **kwargs):
    _recalc(instance.purchase_order_id)
