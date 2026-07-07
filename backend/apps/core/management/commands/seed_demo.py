"""Seed demonstration data for Nexus. See docstring in module body."""
from decimal import Decimal
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Seed realistic Gulf ERP demo data'

    def add_arguments(self, parser):
        parser.add_argument('--company', default='Nexus Demo Co')
        parser.add_argument('--email', default='admin@nexusdemo.com')
        parser.add_argument('--clean', action='store_true')

    def handle(self, *args, **options):
        User = get_user_model()
        from apps.core.models import Company, Branch, Warehouse
        from apps.tenants.onboarding import service

        name = options['company']
        email = options['email']

        if options['clean']:
            Company.objects.filter(name=name).delete()
            User.objects.filter(email=email).delete()
            self.stdout.write(self.style.WARNING('Cleaned existing demo data'))

        try:
            result = service.register(name, email, 'Demo@1234!', 'SA', '300000000000003')
            company = Company.objects.get(pk=result['company_id'])
            user = User.objects.get(pk=result['user_id'])
        except ValueError:
            company = Company.objects.get(name=name)
            user = User.objects.get(email=email)

        service.setup(company, {'seed_coa': True, 'create_warehouse': True,
                                 'seed_currencies': True, 'seed_compliance': True})
        warehouse = Warehouse.objects.filter(branch__company=company).first()

        self._seed_customers(company)
        self._seed_suppliers(company)
        items = self._seed_items(company)
        self._seed_projects(company)
        self._seed_kpis()
        self._seed_journal_entries(company, user)

        status = service.status(company)
        self.stdout.write(self.style.SUCCESS(
            f'✓ Demo seeded: "{name}" — readiness {status["readiness_score"]*100:.0f}%'))
        self.stdout.write(f'  Login: {email} / Demo@1234!')

    def _seed_customers(self, company):
        from apps.selling.models import Customer
        for name, vat in [('Saudi Telecom', '300001'), ('Aramco', '300002'),
                           ('SABIC', '300003'), ('STC Pay', '300004'), ('Elm', '300005')]:
            Customer.objects.get_or_create(company=company, name=name,
                                            defaults={'tax_id': vat})

    def _seed_suppliers(self, company):
        from apps.buying.models import Supplier
        for name, vat in [('3M Saudi Arabia', '310001'), ('Siemens Local', '310002'),
                           ('Oracle ME', '310003'), ('HP Arabia', '310004'), ('Cisco SA', '310005')]:
            Supplier.objects.get_or_create(company=company, name=name,
                                            defaults={'tax_id': vat})

    def _seed_items(self, company):
        from apps.inventory.models import Item
        items = []
        for code, iname, itype, price in [
            ('LAPTOP-001', 'Dell Latitude 5540', 'Product', 3500),
            ('SERVER-001', 'HP ProLiant DL380', 'Product', 25000),
            ('SW-LIC-001', 'Office 365 Business', 'Service', 500),
            ('NETWORK-001', 'Cisco Switch 48-Port', 'Product', 8000),
            ('CONSULT-001', 'IT Consulting/hour', 'Service', 350),
        ]:
            item, _ = Item.objects.get_or_create(
                company=company, item_code=code,
                defaults={'item_name': iname, 'item_type': itype,
                          'standard_selling_rate': Decimal(str(price)),
                          'standard_buying_rate': Decimal(str(int(price * 0.7)))})
            items.append(item)
        return items

    def _seed_projects(self, company):
        from apps.projects.models import Project, Task, Milestone
        for pname, pcode, status in [
            ('Digital Transformation', 'DIG-2026', 'active'),
            ('ERP Go-Live', 'ERP-2026', 'active'),
            ('Cloud Migration', 'CLO-2026', 'planning'),
        ]:
            proj, _ = Project.objects.get_or_create(
                company=company, project_code=pcode,
                defaults={'project_name': pname, 'status': status,
                          'start_date': date.today(),
                          'end_date': date.today() + timedelta(days=180)})
            for j in range(3):
                Task.objects.get_or_create(
                    project=proj, subject=f'Task {j+1}',
                    defaults={'status': 'Open', 'priority': 'Medium'})
            Milestone.objects.get_or_create(
                project=proj, milestone_name='Phase 1',
                defaults={'due_date': date.today() + timedelta(days=90)})

    def _seed_kpis(self):
        from apps.kpi.models import KPIDefinition
        for kpi_id, name, unit, freq, target in [
            ('REV-001', 'Monthly Revenue', 'SAR', 'monthly', 500000),
            ('CUST-001', 'New Customers', 'count', 'monthly', 20),
            ('DSO-001', 'Days Sales Outstanding', 'days', 'monthly', 45),
        ]:
            KPIDefinition.objects.get_or_create(
                kpi_id=kpi_id,
                defaults={'name': name, 'unit': unit,
                          'frequency': freq, 'target_value': target})

    def _seed_journal_entries(self, company, user):
        from apps.accounts.models import Account, JournalEntry
        cash = Account.objects.filter(company=company, account_number='1100').first()
        revenue = Account.objects.filter(company=company, account_number='4100').first()
        if not (cash and revenue):
            return
        for i in range(3):
            try:
                je = JournalEntry.objects.create(
                    company=company, entry_number=f'JE-DEMO-{i+1:04d}',
                    posting_date=date.today() - timedelta(days=i*10),
                    debit_account=cash, credit_account=revenue,
                    amount=Decimal(str((i+1) * 10000)),
                    status='Draft', posted_by=user)
                je.post_to_ledger()
                je.status = 'Submitted'
                je.save(update_fields=['status'])
            except Exception:
                pass
