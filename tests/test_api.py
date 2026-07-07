import pytest

@pytest.mark.django_db
class TestAPI:
    def test_company_list(self, authenticated_client, company):
        response = authenticated_client.get('/api/v1/core/companies/')
        assert response.status_code == 200
        assert len(response.data['results']) >= 1

    def test_items_list(self, authenticated_client):
        response = authenticated_client.get('/api/v1/inventory/items/')
        assert response.status_code == 200
