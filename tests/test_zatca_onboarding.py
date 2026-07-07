"""Tests for ZATCA Phase 2, self-service onboarding, and integration layer."""
import pytest
from decimal import Decimal
from datetime import date

pytestmark = pytest.mark.django_db


# ── ZATCA ──────────────────────────────────────────────────────────────────────
class TestZATCA:
    def test_qr_tlv_encoding(self):
        from apps.selling.zatca import generate_qr
        qr = generate_qr('Test Co', '300000000000003', '2026-07-07',
                          '1150.00', '150.00')
        import base64
        decoded = base64.b64decode(qr)
        # tag 1 = seller name
        assert decoded[0] == 1
        assert decoded[2:2 + decoded[1]] == b'Test Co'

    def test_invoice_xml_structure(self):
        from apps.selling.zatca import ZATCAInvoice, ZATCAInvoiceLine
        inv = ZATCAInvoice(
            invoice_number='INV-001', issue_date=date(2026, 7, 7),
            seller_name='Nexus Co', seller_vat='300000000000003',
            seller_address='Riyadh', buyer_name='Customer',
            invoice_type='simplified')
        inv.lines.append(ZATCAInvoiceLine(
            description='Widget', quantity=Decimal('10'),
            unit_price=Decimal('100')))
        xml = inv.to_ubl_xml()
        assert '<cbc:ID>INV-001</cbc:ID>' in xml
        assert '<cbc:CompanyID>300000000000003</cbc:CompanyID>' in xml
        assert str(inv.subtotal) in xml
        assert str(inv.total_vat) in xml

    def test_invoice_totals(self):
        from apps.selling.zatca import ZATCAInvoice, ZATCAInvoiceLine
        inv = ZATCAInvoice(
            invoice_number='INV-002', issue_date=date(2026, 7, 7),
            seller_name='Co', seller_vat='300', seller_address='',
            buyer_name='B')
        inv.lines.append(ZATCAInvoiceLine('A', Decimal('2'), Decimal('500')))
        inv.lines.append(ZATCAInvoiceLine('B', Decimal('1'), Decimal('200'), Decimal('5')))
        assert inv.subtotal == Decimal('1200.00')
        assert inv.total_vat == Decimal('160.00')  # 1000*15% + 200*5%
        assert inv.total_with_vat == Decimal('1360.00')

    def test_invoice_hash_changes_with_content(self):
        from apps.selling.zatca import ZATCAInvoice, ZATCAInvoiceLine
        inv1 = ZATCAInvoice(
            invoice_number='INV-003', issue_date=date(2026, 7, 7),
            seller_name='Co', seller_vat='300', seller_address='',
            buyer_name='A')
        inv2 = ZATCAInvoice(
            invoice_number='INV-004', issue_date=date(2026, 7, 7),
            seller_name='Co', seller_vat='300', seller_address='',
            buyer_name='B')
        assert inv1.compute_hash() != inv2.compute_hash()


# ── Onboarding ─────────────────────────────────────────────────────────────────
class TestOnboarding:
    def test_register_creates_company_and_user(self):
        from apps.tenants.onboarding import service
        result = service.register(
            company_name='Nexus Demo', admin_email='admin@demo.com',
            admin_password='SecurePass123!', country='SA',
            vat_number='300000000000003')
        assert result['company_id']
        assert result['user_id']
        from apps.core.models import Company
        assert Company.objects.filter(name='Nexus Demo').exists()

    def test_register_duplicate_email_rejected(self):
        from apps.tenants.onboarding import service
        service.register('Co1', 'dup@test.com', 'pass123!', 'SA', '111')
        with pytest.raises(ValueError, match='already registered'):
            service.register('Co2', 'dup@test.com', 'pass456!', 'SA', '222')

    def test_setup_creates_coa_and_warehouse(self, company):
        from apps.tenants.onboarding import service
        result = service.setup(company, {'seed_coa': True, 'create_warehouse': True,
                                         'seed_currencies': False, 'seed_compliance': False})
        from apps.accounts.models import Account
        from apps.core.models import Warehouse
        assert Account.objects.filter(company=company).count() >= 5
        assert Warehouse.objects.filter(branch__company=company).exists()
        assert result['coa'] >= 5

    def test_setup_idempotent(self, company):
        from apps.tenants.onboarding import service
        opts = {'seed_coa': True, 'create_warehouse': True,
                'seed_currencies': False, 'seed_compliance': False}
        r1 = service.setup(company, opts)
        r2 = service.setup(company, opts)
        from apps.accounts.models import Account
        count = Account.objects.filter(company=company).count()
        assert count == r1['coa']   # second call creates nothing new

    def test_import_customers_from_csv(self, company):
        from apps.tenants.onboarding import service
        csv = "name,vat,email\nAcme Corp,300111,acme@corp.com\nBeta Ltd,300222,beta@ltd.com\n"
        result = service.import_csv(company, csv, 'customers')
        assert result['created'] == 2
        assert result['errors'] == []

    def test_status_shows_readiness(self, company):
        from apps.tenants.onboarding import service
        service.setup(company, {'seed_coa': True, 'create_warehouse': True,
                                 'seed_currencies': False, 'seed_compliance': False})
        status = service.status(company)
        assert 'checks' in status
        assert 'readiness_score' in status
        assert status['checks']['chart_of_accounts'] is True
        assert status['checks']['warehouse'] is True


# ── Integration endpoints ────────────────────────────────────────────────────
class TestIntegration:
    def test_onboarding_register_api(self, api_client):
        resp = api_client.post('/api/v1/tenants/onboarding/register/', {
            'company_name': 'API Co', 'admin_email': 'api@co.com',
            'admin_password': 'SecurePass123!', 'country': 'SA'})
        assert resp.status_code == 201
        assert 'company_id' in resp.data

    def test_onboarding_status_requires_auth(self, api_client):
        resp = api_client.get('/api/v1/tenants/onboarding/status/')
        assert resp.status_code in (401, 403)

    def test_onboarding_status_authenticated(self, authenticated_client, company):
        from apps.tenants.onboarding import service
        service.setup(company, {'seed_coa': True, 'create_warehouse': True,
                                 'seed_currencies': False, 'seed_compliance': False})
        resp = authenticated_client.get('/api/v1/tenants/onboarding/status/')
        assert resp.status_code == 200
        assert 'readiness_score' in resp.data
