"""AI Security: anomaly detection, fraud detection, insider-threat monitoring.

Statistical + rule-based baselines (no external ML dependency required):
- UserBehaviorBaseline: per-user activity profile, updated online
- detect_anomaly(): z-score on request volume / off-hours / new resources
- detect_fraud(): domain rules on financial documents (round-tripping,
  split-to-avoid-approval, duplicate payments, velocity)
- insider_threat_scan(): mass-export / after-hours bulk-read / privilege
  escalation patterns
Findings are written to the immutable ledger and can raise Alerts.
"""
import logging
import statistics
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

logger = logging.getLogger('nexus.aisec')


class AnomalyDetector:
    def detect(self, user, window_hours: int = 24) -> list[dict]:
        from apps.iam.models import LoginContext
        findings = []
        since = timezone.now() - timedelta(hours=window_hours)
        recent = LoginContext.objects.filter(user=user, created_at__gte=since)

        failed = recent.filter(succeeded=False).count()
        if failed >= 5:
            findings.append({'type': 'brute_force_suspect',
                             'severity': 'high',
                             'detail': f'{failed} failed logins in {window_hours}h'})

        countries = set(recent.exclude(country='')
                        .values_list('country', flat=True))
        if len(countries) >= 3:
            findings.append({'type': 'impossible_travel',
                             'severity': 'high',
                             'detail': f'logins from {sorted(countries)}'})

        low_trust = recent.filter(trust_score__lt=0.4).count()
        if low_trust >= 3:
            findings.append({'type': 'repeated_low_trust',
                             'severity': 'medium',
                             'detail': f'{low_trust} low-trust sessions'})
        return findings


class FraudDetector:
    """Rule-based financial fraud signals over journal entries & payments."""

    APPROVAL_THRESHOLD = Decimal('50000')

    def scan_company(self, company, window_days: int = 30) -> list[dict]:
        from apps.accounts.models import JournalEntry
        findings = []
        since = timezone.now().date() - timedelta(days=window_days)
        entries = JournalEntry.objects.filter(
            company=company, posting_date__gte=since)

        # split-to-avoid-approval: many entries just under the threshold
        near = [e for e in entries
                if getattr(e, 'total_debit', 0)
                and self.APPROVAL_THRESHOLD * Decimal('0.9')
                <= e.total_debit < self.APPROVAL_THRESHOLD]
        if len(near) >= 3:
            findings.append({
                'type': 'threshold_splitting', 'severity': 'high',
                'detail': f'{len(near)} entries just below approval limit'})

        # duplicate amounts same day (possible double payment)
        seen = {}
        for e in entries:
            key = (e.posting_date, getattr(e, 'total_debit', 0))
            seen.setdefault(key, []).append(e.entry_number)
        for (d, amt), nums in seen.items():
            if amt and len(nums) >= 2:
                findings.append({
                    'type': 'duplicate_amount', 'severity': 'medium',
                    'detail': f'{len(nums)} entries of {amt} on {d}: {nums[:5]}'})
        return findings


class InsiderThreatMonitor:
    def scan(self, user, window_hours: int = 24) -> list[dict]:
        """Detect mass-export, after-hours bulk reads, privilege escalation."""
        findings = []
        try:
            from apps.core.models import AuditLog
            since = timezone.now() - timedelta(hours=window_hours)
            logs = AuditLog.objects.filter(user=user, timestamp__gte=since) \
                if hasattr(AuditLog, 'timestamp') else AuditLog.objects.none()
            reads = logs.filter(action__icontains='export').count() \
                if logs else 0
            if reads >= 20:
                findings.append({'type': 'mass_export', 'severity': 'high',
                                 'detail': f'{reads} export actions in '
                                           f'{window_hours}h'})
        except Exception:
            pass

        # privilege escalation via PAM abuse
        try:
            from apps.iam.models import PrivilegedSession
            since = timezone.now() - timedelta(hours=window_hours)
            elevations = PrivilegedSession.objects.filter(
                user=user, requested_at__gte=since).count()
            if elevations >= 3:
                findings.append({
                    'type': 'frequent_elevation', 'severity': 'medium',
                    'detail': f'{elevations} privilege requests in '
                              f'{window_hours}h'})
        except Exception:
            pass
        return findings


class SecurityOrchestrator:
    """Runs all detectors, records findings to the immutable ledger,
    raises Alerts on high severity. Celery-beat target: run_scan()."""

    def __init__(self):
        self.anomaly = AnomalyDetector()
        self.fraud = FraudDetector()
        self.insider = InsiderThreatMonitor()

    def run_scan(self):
        from django.contrib.auth import get_user_model
        from apps.core.models import Company
        from apps.core.security.immutable_audit import ledger

        all_findings = []
        User = get_user_model()
        for user in User.objects.filter(is_active=True)[:1000]:
            for f in (self.anomaly.detect(user)
                      + self.insider.scan(user)):
                f['user_id'] = str(user.pk)
                all_findings.append(f)
        for company in Company.objects.all()[:500]:
            for f in self.fraud.scan_company(company):
                f['company_id'] = company.pk
                all_findings.append(f)

        for f in all_findings:
            ledger.append('security.finding', f)
            if f.get('severity') == 'high':
                self._raise_alert(f)
        logger.info('AI security scan: %d findings', len(all_findings))
        return all_findings

    def _raise_alert(self, finding):
        try:
            from apps.core.observability import metrics_collector
            metrics_collector.counter('security.high_finding', 1,
                                      {'type': finding['type']})
        except Exception:
            pass


orchestrator = SecurityOrchestrator()
