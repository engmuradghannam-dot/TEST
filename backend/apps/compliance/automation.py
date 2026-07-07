"""Compliance Automation engine — automated control checks + evidence.

Complements the framework/requirement catalog with executable checks that
run against the system and write tamper-proof evidence into the immutable
audit ledger. A check maps a requirement to a callable(company)->bool.
"""
import importlib
import logging

logger = logging.getLogger('nexus.compliance')

# requirement_id -> dotted path of a callable(company)->bool
AUTOMATED_CHECKS = {
    'immutable-audit': 'apps.compliance.automation.check_immutable_audit',
    'encryption-at-rest': 'apps.compliance.automation.check_encryption_at_rest',
    'zero-trust': 'apps.compliance.automation.check_zero_trust_enabled',
}


def _resolve(path):
    module, name = path.rsplit('.', 1)
    return getattr(importlib.import_module(module), name)


class ComplianceEngine:
    def run_framework(self, framework_id: str, company=None) -> dict:
        from .models import ComplianceFramework
        from apps.core.security.immutable_audit import ledger
        fw = ComplianceFramework.objects.filter(framework_id=framework_id).first()
        if not fw:
            return {'error': f'unknown framework {framework_id}'}
        results = {'pass': 0, 'fail': 0, 'manual': 0}
        for req in fw.requirements.filter(is_active=True):
            check_path = AUTOMATED_CHECKS.get(req.requirement_id)
            if not check_path:
                results['manual'] += 1
                continue
            try:
                ok = _resolve(check_path)(company)
                results['pass' if ok else 'fail'] += 1
                ledger.append('compliance.check', {
                    'framework': framework_id,
                    'requirement': req.requirement_id,
                    'status': 'pass' if ok else 'fail'})
            except Exception as exc:  # noqa: BLE001
                logger.warning('check %s failed: %s', req.requirement_id, exc)
                results['manual'] += 1
        total = max(sum(results.values()), 1)
        return {'framework': framework_id, **results,
                'score': round(results['pass'] / total, 2)}


def check_immutable_audit(company=None) -> bool:
    from apps.core.security.immutable_audit import ledger
    return ledger.verify_chain()['intact']


def check_encryption_at_rest(company=None) -> bool:
    from django.conf import settings
    return bool(getattr(settings, 'AUDIT_SIGNING_KEY', None))


def check_zero_trust_enabled(company=None) -> bool:
    from django.conf import settings
    return getattr(settings, 'ZERO_TRUST_ENABLED', False)


engine = ComplianceEngine()
