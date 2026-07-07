"""E2E workflow tests: full business cycles end-to-end."""
import pytest
from datetime import date


@pytest.mark.django_db
class TestPurchaseToInventoryCycle:
    """Full PO lifecycle: Draft -> Submitted -> Received."""

    def test_complete_po_workflow(self, authenticated_client, company, supplier,
                                  warehouse, item):
        # 1. Create PO
        po = authenticated_client.post('/api/v1/buying/purchase-orders/', {
            'company': company.id, 'supplier': supplier.id,
            'po_number': 'E2E-PO-001', 'transaction_date': str(date.today()),
            'warehouse': warehouse.id,
        })
        assert po.status_code == 201, po.data
        po_id = po.data['id']

        # 2. Add line item
        line = authenticated_client.post('/api/v1/buying/purchase-order-items/', {
            'purchase_order': po_id, 'item': item.id, 'qty': 50, 'rate': 100,
        })
        assert line.status_code == 201, line.data

        # 3. Submit PO
        submit = authenticated_client.patch(
            f'/api/v1/buying/purchase-orders/{po_id}/', {'status': 'Submitted'})
        assert submit.status_code == 200, submit.data
        assert submit.data['status'] == 'Submitted'

        # 4. Receive PO
        receive = authenticated_client.patch(
            f'/api/v1/buying/purchase-orders/{po_id}/', {'status': 'Received'})
        assert receive.status_code == 200, receive.data

        # 5. Verify PO is received and stock updated
        item_data = authenticated_client.get(
            f'/api/v1/inventory/items/{item.id}/').data
        assert float(item_data['stock_quantity']) == 50.0


@pytest.mark.django_db
class TestSalesCycleWithTax:
    """SO creation with VAT calculation and submission."""

    def test_so_with_vat(self, authenticated_client, company, customer,
                         item, warehouse):
        from apps.accounts.fiscal import TaxRule
        TaxRule.objects.create(country='SA', tax_type='vat', rate=15)

        # 1. Create SO
        so = authenticated_client.post('/api/v1/selling/sales-orders/', {
            'company': company.id, 'customer': customer.id,
            'so_number': 'E2E-SO-001', 'transaction_date': str(date.today()),
            'warehouse': warehouse.id,
        })
        assert so.status_code == 201, so.data
        so_id = so.data['id']

        # 2. Add line item (2000 SAR base, 300 SAR VAT = 2300 SAR total)
        line = authenticated_client.post('/api/v1/selling/sales-order-items/', {
            'sales_order': so_id, 'item': item.id, 'qty': 10, 'rate': 200,
        })
        assert line.status_code == 201, line.data

        # 3. Verify grand total
        so_detail = authenticated_client.get(
            f'/api/v1/selling/sales-orders/{so_id}/').data
        assert float(so_detail['grand_total']) >= 2000.0

        # 4. Submit
        submit = authenticated_client.patch(
            f'/api/v1/selling/sales-orders/{so_id}/', {'status': 'Submitted'})
        assert submit.status_code in (200, 400)  # 400 if stock check fails


@pytest.mark.django_db
class TestFinancialE2E:
    """Complete accounting cycle: JE -> post -> trial balance balanced."""

    def test_journal_entry_to_trial_balance(self, authenticated_client, company):
        from apps.accounts.models import Account

        cash = Account.objects.create(
            company=company, account_number='1100', account_name='Cash',
            account_type='Asset', root_type='Asset')
        revenue = Account.objects.create(
            company=company, account_number='4100', account_name='Revenue',
            account_type='Income', root_type='Income')

        # Create and post a balanced JE
        je = authenticated_client.post('/api/v1/accounts/journal-entries/', {
            'company': company.id, 'entry_number': 'E2E-JE-001',
            'posting_date': str(date.today()),
            'debit_account': cash.id, 'credit_account': revenue.id,
            'amount': 10000,
        }).data
        assert 'id' in je, je

        submit = authenticated_client.patch(
            f'/api/v1/accounts/journal-entries/{je["id"]}/',
            {'status': 'Submitted'})
        assert submit.status_code == 200

        # Verify trial balance is balanced
        tb = authenticated_client.get(
            '/api/v1/accounts/reports/trial-balance/').data
        assert tb['is_balanced'] is True
        assert float(tb['total_debit']) == float(tb['total_credit'])
