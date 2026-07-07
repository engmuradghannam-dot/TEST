import pytest
from django.test import Client

@pytest.mark.django_db
def test_api_health_check():
    client = Client()
    response = client.get('/api/v1/')
    assert response.status_code in [200, 401, 403]  # auth required

@pytest.mark.django_db
def test_auth_token_endpoint():
    client = Client()
    response = client.post('/api/v1/auth-token/', {'username': 'test', 'password': 'test'})
    assert response.status_code in [200, 400]  # 400 if user doesn't exist
