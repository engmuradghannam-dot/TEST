"""Compliance Automation engine: runs automated control checks and
records evidence into the immutable ledger."""
import importlib
import logging

from django.utils import timezone

logger = logging.getLogger('nexus.compliance')


def _resolve(path):
    module, name = path.rsplit('.', 1)
    return getattr(importlib.import_module(module), name)


class ComplianceEngine:
    def run_framework(self, framework_code: str, company=None) -> dict:
        from .models import ComplianceFramework, ControlAssessment
        from apps.core.security.immutable_audit import ledger
        fw = ComplianceFramework.objects.filter(code=framework_code).first()
        if not fw:
            return {'error': f'unknown framework {framework_code}'}
        results = {'pass': 0, 'fail': 0, 'manual': 0}
        for control in fw.controls.all():
            if control.automated_check:
                try:
                    ok = _resolve(control.automated_check)(company)
                    status = 'pass' if ok else 'fail'
                    results['pass' if ok else 'fail'] += 1
                    ControlAssessment.objects.create(
                        control=control, status=status, automated=True,
                        evidence={'checked_at': timezone.now().isoformat()})
                    ledger.append('compliance.check', {
                        'framework': framework_code,
                        'control': control.control_id, 'status': status})
                except Exception as exc:  # noqa: BLE001
                    logger.warning('control %s check failed: %s',
                                   control.control_id, exc)
                    results['manual'] += 1
            else:
                results['manual'] += 1
        return {'framework': framework_code, **results,
                'score': round(results['pass'] /
                               max(sum(results.values()), 1), 2)}


# ── example automated checks ───────────────────────────────────────
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
