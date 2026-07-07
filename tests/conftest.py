"""Shared pytest fixtures for the Nexus-Framework test suite."""
import os
import pytest

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexus.settings_test')


# ── API clients ───────────────────────────────────────────────────────────────
@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


class _AuthClient:
    """Wraps APIClient so it can be used directly (client.post(...))
    AND unpacked as a tuple (client, user) for backward-compat with
    tests written before this fixture existed."""
    def __init__(self, client, user):
        self._client = client
        self.user = user

    # forward all attribute lookups to the real client
    def __getattr__(self, item):
        return getattr(self._client, item)

    # tuple unpacking: client, user = authenticated_client
    def __iter__(self):
        return iter((self._client, self.user))


@pytest.fixture
def user(django_user_model, company):
    u = django_user_model.objects.create_user(
        email='test@example.com', password='testpass123',
        first_name='Test', last_name='User')
    # make staff so is_staff/is_superuser checks in viewsets pass
    u.is_staff = True
    try:
        u.company = company
        update_fields = ['is_staff']
        if hasattr(u.__class__, 'company'): update_fields.append('company')
        u.save(update_fields=update_fields)
    except Exception:
        u.save()
    return u


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return _AuthClient(api_client, user)


# ── core entities ─────────────────────────────────────────────────────────────
@pytest.fixture
def company(db):
    from apps.core.models import Company
    return Company.objects.create(
        name='Test Company', tax_id='300000000000003', email='company@test.com')


@pytest.fixture
def branch(company):
    from apps.core.models import Branch
    return Branch.objects.create(company=company, name='Main Branch')


@pytest.fixture
def warehouse(company):
    from apps.core.models import Warehouse
    branch_obj, _ = __import__('apps.core.models', fromlist=['Branch']).Branch.objects.get_or_create(
        company=company, name='Main Branch')
    return Warehouse.objects.create(branch=branch_obj, name='Main Warehouse')


@pytest.fixture
def department(company):
    from apps.hr.models import Department
    return Department.objects.create(company=company, name='General')


# ── buying / selling ──────────────────────────────────────────────────────────
@pytest.fixture
def supplier(company):
    from apps.buying.models import Supplier
    return Supplier.objects.create(company=company, name='Test Supplier')


@pytest.fixture
def customer(company):
    from apps.selling.models import Customer
    return Customer.objects.create(company=company, name='Test Customer')


# ── inventory ─────────────────────────────────────────────────────────────────
@pytest.fixture
def item(company):
    from apps.inventory.models import Item
    return Item.objects.create(
        company=company, item_code='ITM-001', item_name='Test Item',
        item_type='Product', valuation_method='FIFO')


# ── HR ────────────────────────────────────────────────────────────────────────
@pytest.fixture
def employee(company, user, department):
    from apps.hr.models import Employee
    from apps.hr.models import Employee as _E
    fields = {f.name for f in _E._meta.fields}
    kwargs = dict(company=company, first_name='Test', last_name='Employee')
    if 'user' in fields: kwargs['user'] = user
    if 'department' in fields: kwargs['department'] = department
    if 'employee_id' in fields: kwargs['employee_id'] = 'EMP-001'
    if 'hire_date' in fields: kwargs['hire_date'] = '2024-01-01'
    if 'employment_type' in fields: kwargs['employment_type'] = 'full_time'
    if 'basic_salary' in fields: kwargs['basic_salary'] = 10000
    return Employee.objects.create(**kwargs)


# ── multi-company / multi-tenant fixtures ────────────────────────────────────
@pytest.fixture
def company2(db):
    from apps.core.models import Company
    return Company.objects.create(
        name='Second Company', tax_id='987654321', email='company2@test.com')


@pytest.fixture
def user2(django_user_model, company2):
    return django_user_model.objects.create_user(
        email='user2@example.com', password='testpass123',
        first_name='User', last_name='Two', company=company2)


@pytest.fixture
def company_client(api_client, user):
    """Authenticated client belonging to `company`."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def company2_client(api_client, user2):
    """Authenticated client belonging to `company2`."""
    api_client.force_authenticate(user=user2)
    return api_client


# ── team / multi-employee fixtures ───────────────────────────────────────────
@pytest.fixture
def employee2(company, department):
    """A second employee in the same company (not linked to a user)."""
    from apps.hr.models import Employee
    from apps.core.models import User
    u2 = User.objects.create_user(
        email='emp2@example.com', password='x',
        first_name='Omar', last_name='Second', company=company)
    fields = {f.name for f in Employee._meta.fields}
    kwargs = dict(company=company, first_name='Omar', last_name='Second')
    if 'user' in fields: kwargs['user'] = u2
    if 'department' in fields: kwargs['department'] = department
    if 'employee_id' in fields: kwargs['employee_id'] = 'EMP-002'
    if 'hire_date' in fields: kwargs['hire_date'] = '2024-01-01'
    if 'employment_type' in fields: kwargs['employment_type'] = 'full_time'
    if 'basic_salary' in fields: kwargs['basic_salary'] = 8000
    return Employee.objects.create(**kwargs)


@pytest.fixture
def company_user(django_user_model, company, employee):
    """A regular (non-staff) user linked to `employee`, for scoping tests."""
    u = employee.user if hasattr(employee, 'user') and employee.user else None
    if u is None:
        u = django_user_model.objects.create_user(
            email='sara@example.com', password='x',
            first_name='Sara', last_name='Employee', company=company)
        from apps.hr.models import Employee as _E
        if hasattr(_E._meta, 'get_field'):
            try:
                employee.user = u
                employee.save(update_fields=['user'])
            except Exception:
                pass
    u.is_staff = False
    u.save(update_fields=['is_staff'])
    return u


@pytest.fixture
def team(company, employee):
    from apps.hr.models import Team
    t = Team.objects.create(company=company, name='Alpha Team')
    t.members.add(employee)
    return t


@pytest.fixture
def superuser(django_user_model, company):
    u = django_user_model.objects.create_superuser(
        email='superuser@example.com', password='superpass123')
    try:
        u.company = company
        u.save()
    except Exception:
        pass
    return u
