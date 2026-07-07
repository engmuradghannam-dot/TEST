import pytest
from datetime import date


@pytest.mark.django_db
class TestPurchaseOrderLogic:
    def _create_po(self, client, company, supplier, warehouse):
        resp = client.post('/api/v1/buying/purchase-orders/', {
            'company': company.id, 'supplier': supplier.id, 'po_number': 'PO-TEST-1',
            'transaction_date': str(date.today()), 'warehouse': warehouse.id,
        })
        assert resp.status_code == 201, resp.data
        return resp.data['id']

    def test_line_item_rejects_zero_quantity(self, authenticated_client, company, supplier, warehouse, item):
        po_id = self._create_po(authenticated_client, company, supplier, warehouse)
        resp = authenticated_client.post('/api/v1/buying/purchase-order-items/', {
            'purchase_order': po_id, 'item': item.id, 'qty': 0, 'rate': 10,
        })
        assert resp.status_code == 400

    def test_amount_and_totals_auto_calculate(self, authenticated_client, company, supplier, warehouse, item):
        po_id = self._create_po(authenticated_client, company, supplier, warehouse)
        resp = authenticated_client.post('/api/v1/buying/purchase-order-items/', {
            'purchase_order': po_id, 'item': item.id, 'qty': 10, 'rate': 25,
        })
        assert resp.status_code == 201
        assert float(resp.data['amount']) == 250.0

        po = authenticated_client.get(f'/api/v1/buying/purchase-orders/{po_id}/').data
        assert float(po['total_qty']) == 10.0
        assert float(po['total_amount']) == 250.0
        assert float(po['grand_total']) == 250.0

    def test_cannot_skip_draft_to_received(self, authenticated_client, company, supplier, warehouse):
        po_id = self._create_po(authenticated_client, company, supplier, warehouse)
        resp = authenticated_client.patch(f'/api/v1/buying/purchase-orders/{po_id}/', {'status': 'Received'})
        assert resp.status_code == 400

    def test_line_locked_after_submit(self, authenticated_client, company, supplier, warehouse, item):
        po_id = self._create_po(authenticated_client, company, supplier, warehouse)
        line = authenticated_client.post('/api/v1/buying/purchase-order-items/', {
            'purchase_order': po_id, 'item': item.id, 'qty': 5, 'rate': 10,
        }).data
        authenticated_client.patch(f'/api/v1/buying/purchase-orders/{po_id}/', {'status': 'Submitted'})
        resp = authenticated_client.patch(f'/api/v1/buying/purchase-order-items/{line["id"]}/', {'qty': 99})
        assert resp.status_code == 400

    def test_receiving_po_increases_stock(self, authenticated_client, company, supplier, warehouse, item):
        po_id = self._create_po(authenticated_client, company, supplier, warehouse)
        authenticated_client.post('/api/v1/buying/purchase-order-items/', {
            'purchase_order': po_id, 'item': item.id, 'qty': 100, 'rate': 20,
        })
        authenticated_client.patch(f'/api/v1/buying/purchase-orders/{po_id}/', {'status': 'Submitted'})
        resp = authenticated_client.patch(f'/api/v1/buying/purchase-orders/{po_id}/', {'status': 'Received'})
        assert resp.status_code == 200

        item_data = authenticated_client.get(f'/api/v1/inventory/items/{item.id}/').data
        assert float(item_data['stock_quantity']) == 100.0


@pytest.mark.django_db
class TestSalesOrderLogic:
    def _stock_item(self, client, company, supplier, warehouse, item, qty):
        po = client.post('/api/v1/buying/purchase-orders/', {
            'company': company.id, 'supplier': supplier.id, 'po_number': f'PO-STOCK-{qty}',
            'transaction_date': str(date.today()), 'warehouse': warehouse.id,
        }).data
        client.post('/api/v1/buying/purchase-order-items/', {
            'purchase_order': po['id'], 'item': item.id, 'qty': qty, 'rate': 10,
        })
        client.patch(f'/api/v1/buying/purchase-orders/{po["id"]}/', {'status': 'Submitted'})
        client.patch(f'/api/v1/buying/purchase-orders/{po["id"]}/', {'status': 'Received'})

    def test_delivering_so_decreases_stock(self, authenticated_client, company, customer, warehouse, item, supplier):
        self._stock_item(authenticated_client, company, supplier, warehouse, item, 100)

        so = authenticated_client.post('/api/v1/selling/sales-orders/', {
            'company': company.id, 'customer': customer.id, 'so_number': 'SO-TEST-1',
            'transaction_date': str(date.today()), 'warehouse': warehouse.id,
        }).data
        authenticated_client.post('/api/v1/selling/sales-order-items/', {
            'sales_order': so['id'], 'item': item.id, 'qty': 30, 'rate': 35,
        })
        authenticated_client.patch(f'/api/v1/selling/sales-orders/{so["id"]}/', {'status': 'Submitted'})
        resp = authenticated_client.patch(f'/api/v1/selling/sales-orders/{so["id"]}/', {'status': 'Delivered'})
        assert resp.status_code == 200

        item_data = authenticated_client.get(f'/api/v1/inventory/items/{item.id}/').data
        assert float(item_data['stock_quantity']) == 70.0

    def test_delivering_more_than_available_is_rejected(self, authenticated_client, company, customer, warehouse, item, supplier):
        self._stock_item(authenticated_client, company, supplier, warehouse, item, 10)

        so = authenticated_client.post('/api/v1/selling/sales-orders/', {
            'company': company.id, 'customer': customer.id, 'so_number': 'SO-TEST-2',
            'transaction_date': str(date.today()), 'warehouse': warehouse.id,
        }).data
        authenticated_client.post('/api/v1/selling/sales-order-items/', {
            'sales_order': so['id'], 'item': item.id, 'qty': 999, 'rate': 35,
        })
        authenticated_client.patch(f'/api/v1/selling/sales-orders/{so["id"]}/', {'status': 'Submitted'})
        resp = authenticated_client.patch(f'/api/v1/selling/sales-orders/{so["id"]}/', {'status': 'Delivered'})
        assert resp.status_code == 400

        item_data = authenticated_client.get(f'/api/v1/inventory/items/{item.id}/').data
        assert float(item_data['stock_quantity']) == 10.0  # untouched
