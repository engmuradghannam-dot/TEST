import pytest


@pytest.mark.django_db
class TestMultiTenancy:
    def test_regular_user_sees_only_own_company(self, company_client, company, company2):
        resp = company_client.get('/api/v1/core/companies/')
        assert resp.status_code == 200
        ids = [c['id'] for c in resp.data['results']]
        assert company.id in ids
        assert company2.id not in ids

    def test_cross_tenant_read_returns_empty(self, company2_client, company, supplier):
        """A user from company2 must not see suppliers belonging to company."""
        resp = company2_client.get('/api/v1/buying/suppliers/')
        assert resp.status_code == 200
        ids = [s['id'] for s in resp.data['results']]
        assert supplier.id not in ids

    def test_cross_tenant_write_is_rejected(self, company2_client, company):
        """A user from company2 must not be able to create records tagged
        with company's id."""
        resp = company2_client.post('/api/v1/buying/suppliers/', {
            'company': company.id, 'name': 'Hacked Supplier',
        })
        assert resp.status_code in (400, 403)

    def test_unauthenticated_request_is_rejected(self, api_client):
        resp = api_client.get('/api/v1/core/companies/')
        assert resp.status_code in (401, 403)

    def test_superuser_sees_all_companies(self, api_client, superuser, company, company2):
        api_client.force_authenticate(user=superuser)
        resp = api_client.get('/api/v1/core/companies/')
        ids = [c['id'] for c in resp.data['results']]
        assert company.id in ids
        assert company2.id in ids
