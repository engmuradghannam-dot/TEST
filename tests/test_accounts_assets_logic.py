import pytest


@pytest.mark.django_db
class TestJournalEntryLogic:
    def test_same_debit_and_credit_account_rejected(self, authenticated_client, company):
        acc = authenticated_client.post('/api/v1/accounts/accounts/', {
            'company': company.id, 'account_name': 'Cash', 'account_number': '1000', 'account_type': 'Asset',
        }).data
        resp = authenticated_client.post('/api/v1/accounts/journal-entries/', {
            'company': company.id, 'entry_number': 'JE-1', 'posting_date': '2026-07-06',
            'debit_account': acc['id'], 'credit_account': acc['id'], 'amount': 100,
        })
        assert resp.status_code == 400

    def test_different_accounts_accepted(self, authenticated_client, company):
        acc1 = authenticated_client.post('/api/v1/accounts/accounts/', {
            'company': company.id, 'account_name': 'Cash', 'account_number': '1000', 'account_type': 'Asset',
        }).data
        acc2 = authenticated_client.post('/api/v1/accounts/accounts/', {
            'company': company.id, 'account_name': 'Sales', 'account_number': '4000', 'account_type': 'Income',
        }).data
        resp = authenticated_client.post('/api/v1/accounts/journal-entries/', {
            'company': company.id, 'entry_number': 'JE-2', 'posting_date': '2026-07-06',
            'debit_account': acc1['id'], 'credit_account': acc2['id'], 'amount': 100,
        })
        assert resp.status_code == 201

    def test_submitted_is_final_state(self, authenticated_client, company):
        acc1 = authenticated_client.post('/api/v1/accounts/accounts/', {
            'company': company.id, 'account_name': 'Cash', 'account_number': '1001', 'account_type': 'Asset',
        }).data
        acc2 = authenticated_client.post('/api/v1/accounts/accounts/', {
            'company': company.id, 'account_name': 'Sales', 'account_number': '4001', 'account_type': 'Income',
        }).data
        je = authenticated_client.post('/api/v1/accounts/journal-entries/', {
            'company': company.id, 'entry_number': 'JE-3', 'posting_date': '2026-07-06',
            'debit_account': acc1['id'], 'credit_account': acc2['id'], 'amount': 100,
        }).data
        authenticated_client.patch(f'/api/v1/accounts/journal-entries/{je["id"]}/', {'status': 'Submitted'})
        resp = authenticated_client.patch(f'/api/v1/accounts/journal-entries/{je["id"]}/', {'status': 'Draft'})
        assert resp.status_code == 400


@pytest.mark.django_db
class TestAssetLogic:
    def test_salvage_exceeding_purchase_value_rejected(self, authenticated_client, company):
        resp = authenticated_client.post('/api/v1/assets/assets/', {
            'company': company.id, 'asset_name': 'Van', 'asset_code': 'AST-1',
            'purchase_value': 1000, 'salvage_value': 5000,
        })
        assert resp.status_code == 400

    def test_valid_asset_accepted_with_depreciation(self, authenticated_client, company):
        resp = authenticated_client.post('/api/v1/assets/assets/', {
            'company': company.id, 'asset_name': 'Van', 'asset_code': 'AST-2',
            'purchase_date': '2020-01-01', 'purchase_value': 100000, 'salvage_value': 10000,
            'depreciation_method': 'Straight Line', 'depreciation_rate': 20,
        })
        assert resp.status_code == 201
        assert float(resp.data['accumulated_depreciation']) > 0
        assert float(resp.data['book_value']) < 100000
