"""Self-service tenant onboarding: registration → setup wizard → go live.

Flow:
1. POST /api/v1/onboarding/register/        -> creates Tenant + admin user
2. POST /api/v1/onboarding/setup/           -> seeds COA, warehouses, currencies
3. POST /api/v1/onboarding/import-data/     -> imports CSV data (customers/items)
4. GET  /api/v1/onboarding/status/          -> readiness checklist

All steps are idempotent; each can be called multiple times safely.
"""
import logging

from django.contrib.auth import get_user_model
from django.db import transaction

logger = logging.getLogger('nexus.onboarding')


class OnboardingService:

    # ── Step 1: Register ──────────────────────────────────────────────────
    @transaction.atomic
    def register(self, company_name: str, admin_email: str,
                 admin_password: str, country: str = 'SA',
                 vat_number: str = '') -> dict:
        from apps.core.models import Company
        User = get_user_model()

        if User.objects.filter(email=admin_email).exists():
            raise ValueError(f"Email {admin_email} is already registered")

        company = Company.objects.create(
            name=company_name, email=admin_email,
            tax_id=vat_number, country=country)
        user = User.objects.create_user(
            email=admin_email, password=admin_password,
            first_name='Admin', last_name=company_name,
            is_staff=True)
        user.company = company
        user.save(update_fields=['company'])
        logger.info('registered new company %s (id=%s)', company_name, company.pk)
        return {'company_id': company.pk, 'user_id': user.pk}

    # ── Step 2: Setup wizard ──────────────────────────────────────────────
    @transaction.atomic
    def setup(self, company, options: dict | None = None) -> dict:
        opts = options or {}
        results = {}

        # Seed chart of accounts
        if opts.get('seed_coa', True):
            results['coa'] = self._seed_coa(company)

        # Seed currencies
        if opts.get('seed_currencies', True):
            try:
                from django.core.management import call_command
                call_command('seed_localization', verbosity=0)
                results['currencies'] = 'seeded'
            except Exception as e:
                results['currencies'] = f'skipped: {e}'

        # Seed compliance frameworks
        if opts.get('seed_compliance', True):
            try:
                from django.core.management import call_command
                call_command('seed_compliance', verbosity=0)
                results['compliance'] = 'seeded'
            except Exception as e:
                results['compliance'] = f'skipped: {e}'

        # Create default warehouse and branch
        if opts.get('create_warehouse', True):
            results['warehouse'] = self._create_defaults(company)

        return results

    def _seed_coa(self, company) -> int:
        """Create a Saudi GAAP-aligned chart of accounts."""
        from apps.accounts.models import Account
        ACCOUNTS = [
            ('1000', 'Current Assets', 'Asset', None, True),
            ('1100', 'Cash and Bank', 'Asset', '1000', False),
            ('1200', 'Accounts Receivable', 'Asset', '1000', False),
            ('1300', 'Inventory', 'Asset', '1000', False),
            ('2000', 'Current Liabilities', 'Liability', None, True),
            ('2100', 'Accounts Payable', 'Liability', '2000', False),
            ('2200', 'VAT Payable', 'Liability', '2000', False),
            ('3000', 'Equity', 'Equity', None, True),
            ('3100', 'Share Capital', 'Equity', '3000', False),
            ('3900', 'Retained Earnings', 'Equity', '3000', False),
            ('4000', 'Revenue', 'Income', None, True),
            ('4100', 'Sales Revenue', 'Income', '4000', False),
            ('5000', 'Cost of Sales', 'Expense', None, True),
            ('5100', 'Cost of Goods Sold', 'Expense', '5000', False),
            ('6000', 'Operating Expenses', 'Expense', None, True),
            ('6100', 'Rent Expense', 'Expense', '6000', False),
            ('6200', 'Salaries Expense', 'Expense', '6000', False),
        ]
        created = 0
        code_to_obj = {}
        for code, name, atype, parent_code, is_group in ACCOUNTS:
            if Account.objects.filter(company=company, account_number=code).exists():
                continue
            parent = code_to_obj.get(parent_code)
            obj = Account.objects.create(
                company=company, account_number=code, account_name=name,
                account_type=atype, root_type=atype, is_group=is_group,
                parent_account=parent)
            code_to_obj[code] = obj
            created += 1
        return created

    def _create_defaults(self, company) -> dict:
        from apps.core.models import Branch, Warehouse
        branch, _ = Branch.objects.get_or_create(
            company=company, name='Main Branch')
        warehouse, _ = Warehouse.objects.get_or_create(
            branch=branch, name='Main Warehouse')
        return {'branch_id': branch.pk, 'warehouse_id': warehouse.pk}

    # ── Step 3: Import data ───────────────────────────────────────────────
    def import_csv(self, company, csv_text: str, entity: str) -> dict:
        import csv, io
        reader = csv.DictReader(io.StringIO(csv_text))
        rows = list(reader)
        created, errors = 0, []
        for i, row in enumerate(rows):
            try:
                if entity == 'customers':
                    from apps.selling.models import Customer
                    Customer.objects.get_or_create(
                        company=company, name=row.get('name', f'Customer {i}'),
                        defaults={'tax_id': row.get('vat', ''),
                                  'email': row.get('email', '')})
                elif entity == 'suppliers':
                    from apps.buying.models import Supplier
                    Supplier.objects.get_or_create(
                        company=company, name=row.get('name', f'Supplier {i}'),
                        defaults={'tax_id': row.get('vat', ''),
                                  'email': row.get('email', '')})
                elif entity == 'items':
                    from apps.inventory.models import Item
                    code = row.get('code', f'ITEM-{i:04d}')
                    Item.objects.get_or_create(
                        company=company, item_code=code,
                        defaults={'item_name': row.get('name', code),
                                  'item_type': 'Product'})
                created += 1
            except Exception as exc:
                errors.append({'row': i + 1, 'error': str(exc)})
        return {'entity': entity, 'rows': len(rows),
                'created': created, 'errors': errors}

    # ── Step 4: Readiness checklist ───────────────────────────────────────
    def status(self, company) -> dict:
        from apps.accounts.models import Account
        from apps.core.models import Branch, Warehouse
        checks = {
            'company_profile': bool(company.tax_id and company.email),
            'chart_of_accounts': Account.objects.filter(
                company=company).count() >= 5,
            'warehouse': Warehouse.objects.filter(
                branch__company=company).exists(),
            'branch': Branch.objects.filter(company=company).exists(),
        }
        try:
            from apps.accounts.fiscal import Currency
            checks['currencies'] = Currency.objects.exists()
        except Exception:
            checks['currencies'] = False
        try:
            from apps.compliance.models import ComplianceFramework
            checks['compliance_seeded'] = ComplianceFramework.objects.exists()
        except Exception:
            checks['compliance_seeded'] = False
        score = sum(checks.values()) / len(checks)
        return {
            'company_id': company.pk,
            'checks': checks,
            'readiness_score': round(score, 2),
            'ready': score >= 0.85,
        }


service = OnboardingService()
