import pytest


@pytest.mark.django_db
class TestGeneralLedger:
    def _make_accounts(self, client, company):
        cash = client.post('/api/v1/accounts/accounts/', {
            'company': company.id, 'account_name': 'Cash', 'account_number': '1001',
            'account_type': 'Asset', 'root_type': 'Asset',
        }).data
        sales = client.post('/api/v1/accounts/accounts/', {
            'company': company.id, 'account_name': 'Sales', 'account_number': '4001',
            'account_type': 'Income', 'root_type': 'Income',
        }).data
        return cash, sales

    def test_posting_journal_entry_updates_account_balances(self, authenticated_client, company):
        cash, sales = self._make_accounts(authenticated_client, company)
        je = authenticated_client.post('/api/v1/accounts/journal-entries/', {
            'company': company.id, 'entry_number': 'JE-1', 'posting_date': '2026-07-06',
            'debit_account': cash['id'], 'credit_account': sales['id'], 'amount': 5000,
        }).data
        resp = authenticated_client.patch(f'/api/v1/accounts/journal-entries/{je["id"]}/', {'status': 'Submitted'})
        assert resp.status_code == 200

        cash_after = authenticated_client.get(f'/api/v1/accounts/accounts/{cash["id"]}/').data
        sales_after = authenticated_client.get(f'/api/v1/accounts/accounts/{sales["id"]}/').data
        assert float(cash_after['balance']) == 5000.0   # Asset: debit increases
        assert float(sales_after['balance']) == 5000.0  # Income: credit increases

    def test_trial_balance_is_balanced(self, authenticated_client, company):
        cash, sales = self._make_accounts(authenticated_client, company)
        je = authenticated_client.post('/api/v1/accounts/journal-entries/', {
            'company': company.id, 'entry_number': 'JE-2', 'posting_date': '2026-07-06',
            'debit_account': cash['id'], 'credit_account': sales['id'], 'amount': 3000,
        }).data
        authenticated_client.patch(f'/api/v1/accounts/journal-entries/{je["id"]}/', {'status': 'Submitted'})

        resp = authenticated_client.get(f'/api/v1/accounts/reports/trial-balance/')
        assert resp.status_code == 200
        assert resp.data['is_balanced'] is True
        assert float(resp.data['total_debit']) == float(resp.data['total_credit'])

    def test_financial_statements_balance_sheet_balances(self, authenticated_client, company):
        cash, sales = self._make_accounts(authenticated_client, company)
        je = authenticated_client.post('/api/v1/accounts/journal-entries/', {
            'company': company.id, 'entry_number': 'JE-3', 'posting_date': '2026-07-06',
            'debit_account': cash['id'], 'credit_account': sales['id'], 'amount': 2000,
        }).data
        authenticated_client.patch(f'/api/v1/accounts/journal-entries/{je["id"]}/', {'status': 'Submitted'})

        resp = authenticated_client.get(f'/api/v1/accounts/reports/income-statement/')
        assert resp.status_code == 200
        assert float(resp.data['net_profit']) == 2000.0
        # verify balance sheet separately
        bs = authenticated_client.get(f'/api/v1/accounts/reports/balance-sheet/')
        assert bs.status_code == 200
        assert bs.data['is_balanced'] is True

    def test_cannot_post_to_group_account(self, authenticated_client, company):
        group_acc = authenticated_client.post('/api/v1/accounts/accounts/', {
            'company': company.id, 'account_name': 'Assets (Header)', 'account_number': '1000',
            'account_type': 'Asset', 'root_type': 'Asset', 'is_group': True,
        }).data
        sales = authenticated_client.post('/api/v1/accounts/accounts/', {
            'company': company.id, 'account_name': 'Sales', 'account_number': '4002',
            'account_type': 'Income', 'root_type': 'Income',
        }).data
        je = authenticated_client.post('/api/v1/accounts/journal-entries/', {
            'company': company.id, 'entry_number': 'JE-4', 'posting_date': '2026-07-06',
            'debit_account': group_acc['id'], 'credit_account': sales['id'], 'amount': 1000,
        }).data
        resp = authenticated_client.patch(f'/api/v1/accounts/journal-entries/{je["id"]}/', {'status': 'Submitted'})
        assert resp.status_code == 400
