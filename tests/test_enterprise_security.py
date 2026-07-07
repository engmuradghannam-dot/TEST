"""Enterprise security + AI-core tests.

Covers the pieces added for the 10/10 push:
- immutable audit ledger: hash chain + signature + tamper detection
- PAM: elevation lifecycle, no self-approval
- role mining: clusters shared permission sets
- predictive: forecast math (trend, bands, confidence)
- decision engine: priority resolution + explainability
- knowledge graph: impact traversal
- compliance automation: automated control checks
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

pytestmark = pytest.mark.django_db


# ── immutable audit ledger ───────────────────────────────────────────
class TestImmutableAudit:
    def test_chain_grows_and_verifies(self):
        from apps.core.security.immutable_audit import ledger, AuditLedgerEntry
        for i in range(5):
            ledger.append('test.event', {'i': i})
        assert AuditLedgerEntry.objects.count() == 5
        result = ledger.verify_chain()
        assert result['intact'] is True
        assert result['verified'] == 5

    def test_entries_are_immutable(self):
        from apps.core.security.immutable_audit import ledger
        e = ledger.append('test.event', {'x': 1})
        with pytest.raises(ValueError, match='immutable'):
            e.payload = {'x': 2}
            e.save()
        with pytest.raises(ValueError, match='cannot be deleted'):
            e.delete()

    def test_tampering_breaks_chain(self):
        from apps.core.security.immutable_audit import ledger, AuditLedgerEntry
        ledger.append('a', {'v': 1})
        target = ledger.append('b', {'v': 2})
        ledger.append('c', {'v': 3})
        # tamper directly via queryset update (bypasses model guard)
        AuditLedgerEntry.objects.filter(pk=target.pk).update(
            payload={'v': 999})
        result = ledger.verify_chain()
        assert result['intact'] is False
        assert any(b['sequence'] == target.sequence for b in result['broken'])

    def test_evidence_export(self):
        from apps.core.security.immutable_audit import ledger
        ledger.append('compliance.x', {'k': 'v'})
        bundle = ledger.export_evidence(event_prefix='compliance.')
        assert bundle['entry_count'] == 1
        assert bundle['chain_verification']['intact'] is True


# ── privileged access management ─────────────────────────────────────
class TestPAM:
    def test_elevation_lifecycle(self, django_user_model, company):
        from apps.iam import pam
        user = django_user_model.objects.create_user(
            email='pam@test.com', password='x')
        approver = django_user_model.objects.create_user(
            email='approver@test.com', password='x', is_staff=True)

        session = pam.request_elevation(user, 'billing_admin',
                                        'month-end close', 30)
        assert session.status == 'requested'
        assert 'billing_admin' not in pam.active_privileges(user)

        session.approve(approver)
        assert session.status == 'active'
        assert session.is_currently_active
        assert 'billing_admin' in pam.active_privileges(user)

    def test_no_self_approval(self, django_user_model):
        from apps.iam import pam
        user = django_user_model.objects.create_user(
            email='self@test.com', password='x', is_staff=True)
        session = pam.request_elevation(user, 'db_operator', 'fix', 15)
        with pytest.raises(ValueError, match='Self-approval'):
            session.approve(user)

    def test_expiry_sweep(self, django_user_model):
        from apps.iam import pam
        from apps.iam.models import PrivilegedSession
        user = django_user_model.objects.create_user(
            email='exp@test.com', password='x')
        s = pam.request_elevation(user, 'role', 'x', 60)
        s.status = 'active'
        s.expires_at = timezone.now() - timedelta(minutes=1)
        s.save()
        assert pam.expire_stale_sessions() == 1
        s.refresh_from_db()
        assert s.status == 'expired'


# ── role mining ──────────────────────────────────────────────────────
class TestRoleMining:
    def test_mines_shared_permission_sets(self, django_user_model):
        from django.contrib.auth.models import Permission
        from apps.iam import pam
        perms = list(Permission.objects.all()[:4])
        # three users share the same 3 permissions -> should be mined
        for i in range(3):
            u = django_user_model.objects.create_user(
                email=f'rm{i}@test.com', password='x')
            u.user_permissions.set(perms[:3])
        report = pam.mine_roles(min_support=2)
        assert report.users_analyzed >= 3
        assert any(len(s['permissions']) >= 3 and s['user_count'] >= 2
                   for s in report.suggestions)


# ── predictive intelligence ──────────────────────────────────────────
class TestPredictive:
    def test_linear_trend_forecast(self):
        from apps.core.intelligence.predictive import forecast_series
        # clean upward trend 10,20,30,40,50 -> next ~60
        r = forecast_series([10, 20, 30, 40, 50], periods=2)
        assert r['method'] == 'linear_trend'
        assert 55 <= r['forecast'][0] <= 65
        assert r['lower'][0] <= r['forecast'][0] <= r['upper'][0]
        assert r['confidence'] > 0.8       # near-perfect line

    def test_short_history_falls_back(self):
        from apps.core.intelligence.predictive import forecast_series
        r = forecast_series([42], periods=3)
        assert r['method'] == 'naive_last'
        assert r['forecast'] == [42, 42, 42]

    def test_forecast_never_negative(self):
        from apps.core.intelligence.predictive import forecast_series
        r = forecast_series([100, 70, 40, 10], periods=3)
        assert all(v >= 0 for v in r['forecast'])
        assert all(v >= 0 for v in r['lower'])


# ── decision engine ──────────────────────────────────────────────────
class TestDecisionEngine:
    def test_priority_resolution_and_explainability(self):
        from apps.core.intelligence.decision_engine import engine
        # small PO -> auto-approve (highest priority rule wins)
        d = engine.decide('po_approval', {'amount': 1000})
        assert d['decision']['action'] == 'auto_approve'
        assert d['rule'] == 'auto_approve_small'
        assert isinstance(d['explanation'], list)

    def test_routing_by_amount(self):
        from apps.core.intelligence.decision_engine import engine
        assert engine.decide('po_approval',
                             {'amount': 20000})['decision']['to'] == 'manager'
        assert engine.decide('po_approval',
                             {'amount': 90000})['decision']['to'] == 'cfo'

    def test_no_match_is_explained(self):
        from apps.core.intelligence.decision_engine import engine, Rule
        engine.define('demo', [Rule('never', [('x', '==', 1)], {'a': 1})])
        d = engine.decide('demo', {'x': 2})
        assert d['decision'] == 'no_match'
        assert d['explanation'][0]['matched'] is False


# ── knowledge graph ──────────────────────────────────────────────────
class TestKnowledgeGraph:
    def test_impact_traversal(self):
        from apps.core.intelligence.knowledge_graph import graph
        supplier = graph.upsert_node('supplier', 'S1', 'Acme')
        item = graph.upsert_node('item', 'I1', 'Widget')
        order = graph.upsert_node('sales_order', 'O1', 'SO-100')
        graph.link(supplier, item, 'supplies')
        graph.link(item, order, 'ordered_in')

        impact = graph.impact_of(supplier, max_depth=3)
        labels = {i['node'] for i in impact}
        assert 'item:Widget' in labels
        assert 'sales_order:SO-100' in labels     # reached at depth 2


# ── compliance automation ────────────────────────────────────────────
class TestComplianceAutomation:
    def test_automated_control_check(self):
        from apps.compliance.models import (ComplianceFramework,
                                            ComplianceControl)
        from apps.compliance.automation import engine
        fw = ComplianceFramework.objects.create(code='soc2', name='SOC 2')
        ComplianceControl.objects.create(
            framework=fw, control_id='CC6.1', title='Audit integrity',
            automated_check='apps.compliance.automation.check_immutable_audit')
        ComplianceControl.objects.create(
            framework=fw, control_id='CC6.7', title='Encryption config',
            automated_check='apps.compliance.automation.check_encryption_at_rest')
        result = engine.run_framework('soc2')
        assert result['pass'] == 2
        assert result['score'] == 1.0
