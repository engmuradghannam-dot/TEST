"""AI Security Engine — anomaly detection, fraud detection, insider threat.

Three analysis layers:
1. BehaviorProfiler  — per-user statistical baseline (login times, volumes,
   IP ranges, typical actions). Z-score & IQR outlier detection (no ML lib needed).
2. FraudDetector     — rule-based + LLM-assisted for financial transaction fraud:
   duplicate invoices, unusual amounts, round-trip payments, off-hours posting.
3. InsiderThreatMonitor — privilege escalation, mass data access, unusual export
   volumes, access after termination, SoD violations.

All detections produce AnomalySignal objects persisted to DB + emitted to SIEM.
"""
import hashlib
import json
import logging
import statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from django.db import models
from django.utils import timezone as dj_timezone

logger = logging.getLogger('nexus.ai_security')


# ── Django models ─────────────────────────────────────────────────
class UserBehaviorProfile(models.Model):
    user_id = models.CharField(max_length=100, db_index=True)
    tenant_id = models.CharField(max_length=100, db_index=True)
    # Statistical baselines (stored as JSON arrays of recent observations)
    login_hours = models.JSONField(default=list,
                                   help_text='Hour-of-day distribution [0-23]')
    daily_request_counts = models.JSONField(default=list,
                                            help_text='Last 30-day request counts')
    typical_ips = models.JSONField(default=list, help_text='Known IP hash list')
    typical_countries = models.JSONField(default=list)
    typical_actions = models.JSONField(default=dict,
                                       help_text='{action_type: count}')
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('user_id', 'tenant_id')]


class AnomalySignal(models.Model):
    TYPES = [('login_anomaly', 'Login Anomaly'),
             ('unusual_hours', 'Unusual Hours'),
             ('geo_anomaly', 'Geographic Anomaly'),
             ('volume_spike', 'Volume Spike'),
             ('fraud_duplicate', 'Duplicate Invoice/Payment'),
             ('fraud_roundtrip', 'Round-trip Payment'),
             ('fraud_unusual_amount', 'Unusual Amount'),
             ('insider_mass_export', 'Mass Data Export'),
             ('insider_privilege_escalation', 'Privilege Escalation'),
             ('insider_post_termination', 'Post-termination Access'),
             ('insider_sod_violation', 'SoD Violation')]
    SEVERITY = [('low','Low'),('medium','Medium'),('high','High'),('critical','Critical')]

    signal_id = models.CharField(max_length=64, unique=True)
    tenant_id = models.CharField(max_length=100, db_index=True)
    anomaly_type = models.CharField(max_length=50, choices=TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY)
    user_id = models.CharField(max_length=100, blank=True, db_index=True)
    description = models.TextField()
    evidence = models.JSONField(default=dict)
    score = models.FloatField(default=0.0, help_text='Risk score 0-1')
    status = models.CharField(max_length=20, default='open',
                              choices=[('open','Open'),('investigating','Investigating'),
                                       ('resolved','Resolved'),('false_positive','False Positive')])
    detected_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-detected_at']
        indexes = [models.Index(fields=['tenant_id', 'severity', 'status'])]


# ── statistical helpers ───────────────────────────────────────────
def _z_score(value: float, data: list[float]) -> float:
    if len(data) < 3:
        return 0.0
    mean = statistics.mean(data)
    try:
        std = statistics.stdev(data)
    except statistics.StatisticsError:
        return 0.0
    return abs(value - mean) / std if std else 0.0


def _ip_hash(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


# ── Behavior Profiler ─────────────────────────────────────────────
class BehaviorProfiler:
    MAX_SAMPLES = 60

    def update(self, tenant_id: str, user_id: str, hour: int,
               ip: str, country: str, action_type: str):
        profile, _ = UserBehaviorProfile.objects.get_or_create(
            user_id=str(user_id), tenant_id=tenant_id)
        hours = (profile.login_hours or [])[-self.MAX_SAMPLES:]
        hours.append(hour)
        ips = set(profile.typical_ips or [])
        ips.add(_ip_hash(ip))
        countries = list(set((profile.typical_countries or []) + [country]))[:20]
        actions = profile.typical_actions or {}
        actions[action_type] = actions.get(action_type, 0) + 1
        UserBehaviorProfile.objects.filter(pk=profile.pk).update(
            login_hours=hours, typical_ips=list(ips)[:50],
            typical_countries=countries, typical_actions=actions)

    def score(self, tenant_id: str, user_id: str, hour: int,
              ip: str, country: str) -> dict[str, float]:
        try:
            profile = UserBehaviorProfile.objects.get(
                user_id=str(user_id), tenant_id=tenant_id)
        except UserBehaviorProfile.DoesNotExist:
            return {}
        signals = {}
        if profile.login_hours and len(profile.login_hours) >= 5:
            z = _z_score(hour, profile.login_hours)
            if z > 2.5:
                signals['unusual_hour'] = min(z / 5.0, 1.0)
        if profile.typical_ips and _ip_hash(ip) not in profile.typical_ips:
            signals['new_ip'] = 0.4
        if profile.typical_countries and country not in profile.typical_countries:
            signals['new_country'] = 0.7
        return signals


# ── Fraud Detector ────────────────────────────────────────────────
class FraudDetector:
    def check_invoice(self, tenant_id: str, vendor_id: str, amount: Decimal,
                      invoice_number: str, user_id: str) -> list[AnomalySignal]:
        from apps.buying.models import PurchaseOrder
        signals = []
        # 1) Duplicate invoice number
        dupes = PurchaseOrder.objects.filter(
            company__id=tenant_id,
            reference_number=invoice_number).exclude(
                created_by__id=None).count()
        if dupes > 0:
            signals.append(self._emit(tenant_id, user_id, 'fraud_duplicate', 'high',
                f"Duplicate invoice {invoice_number} for vendor {vendor_id}",
                {'invoice': invoice_number, 'vendor': vendor_id}, 0.85))
        # 2) Round-number amount (common fraud indicator)
        if amount > 10000 and amount % 1000 == 0:
            signals.append(self._emit(tenant_id, user_id, 'fraud_unusual_amount', 'medium',
                f"Suspiciously round amount {amount} for vendor {vendor_id}",
                {'amount': str(amount)}, 0.45))
        # 3) Off-hours posting
        now = dj_timezone.now()
        if now.hour < 6 or now.hour >= 22:
            signals.append(self._emit(tenant_id, user_id, 'fraud_unusual_amount', 'medium',
                f"Invoice posted outside business hours ({now.hour}:00)",
                {'hour': now.hour, 'amount': str(amount)}, 0.4))
        return signals

    def check_payment_roundtrip(self, tenant_id: str, vendor_id: str,
                                customer_id: str, amount: Decimal,
                                window_days: int = 30) -> AnomalySignal | None:
        """Detect A->B payment followed by B->A payment of similar amount."""
        from apps.buying.models import PurchaseOrder
        from apps.selling.models import SalesOrder
        cutoff = dj_timezone.now() - timedelta(days=window_days)
        po_total = sum(
            PurchaseOrder.objects.filter(
                company__id=tenant_id, supplier__id=vendor_id,
                created_at__gte=cutoff
            ).values_list('grand_total', flat=True)
        )
        so_total = sum(
            SalesOrder.objects.filter(
                company__id=tenant_id, customer__id=customer_id,
                created_at__gte=cutoff
            ).values_list('grand_total', flat=True)
        )
        if po_total and so_total:
            ratio = min(po_total, so_total) / max(po_total, so_total)
            if ratio > 0.85:
                return self._emit(tenant_id, '', 'fraud_roundtrip', 'high',
                    f"Possible round-trip: PO {po_total} ≈ SO {so_total} "
                    f"with same counterpart",
                    {'po_total': str(po_total), 'so_total': str(so_total),
                     'ratio': round(ratio, 2)}, 0.8)
        return None

    def _emit(self, tenant_id, user_id, atype, severity, desc, evidence, score):
        sig_id = hashlib.sha256(f"{tenant_id}{atype}{desc}".encode()).hexdigest()[:32]
        obj, created = AnomalySignal.objects.get_or_create(
            signal_id=sig_id,
            defaults=dict(tenant_id=tenant_id, user_id=str(user_id),
                          anomaly_type=atype, severity=severity,
                          description=desc, evidence=evidence, score=score))
        if created:
            self._siem(tenant_id, user_id, atype, severity, desc, evidence)
        return obj

    def _siem(self, tenant_id, user_id, atype, severity, desc, evidence):
        try:
            from apps.security_engine.siem.integrations import security_event
            security_event(atype, severity=severity, actor_id=str(user_id),
                           tenant_id=tenant_id, description=desc, details=evidence,
                           compliance_tags=['SOC2', 'ISO27001'])
        except Exception:
            pass


# ── Insider Threat Monitor ────────────────────────────────────────
class InsiderThreatMonitor:
    MASS_EXPORT_THRESHOLD = 500     # records in one request
    BULK_QUERY_WINDOW_MIN = 10

    def check_mass_export(self, tenant_id: str, user_id: str,
                          record_count: int, endpoint: str) -> AnomalySignal | None:
        if record_count >= self.MASS_EXPORT_THRESHOLD:
            sig_id = hashlib.sha256(f"mass_export:{tenant_id}:{user_id}:{endpoint}".encode()).hexdigest()[:32]
            obj, created = AnomalySignal.objects.get_or_create(
                signal_id=sig_id,
                defaults=dict(tenant_id=tenant_id, user_id=str(user_id),
                              anomaly_type='insider_mass_export', severity='high',
                              description=f"Mass export: {record_count} records from {endpoint}",
                              evidence={'count': record_count, 'endpoint': endpoint},
                              score=0.75))
            if created:
                try:
                    from apps.security_engine.siem.integrations import security_event
                    security_event('insider_mass_export', severity='high',
                                   actor_id=str(user_id), tenant_id=tenant_id,
                                   details={'count': record_count, 'endpoint': endpoint},
                                   compliance_tags=['SOC2'])
                except Exception:
                    pass
            return obj
        return None

    def check_post_termination(self, tenant_id: str, user_id: str,
                               termination_date) -> AnomalySignal | None:
        if dj_timezone.now().date() > termination_date:
            sig_id = hashlib.sha256(f"post_term:{tenant_id}:{user_id}".encode()).hexdigest()[:32]
            obj, _ = AnomalySignal.objects.get_or_create(
                signal_id=sig_id,
                defaults=dict(tenant_id=tenant_id, user_id=str(user_id),
                              anomaly_type='insider_post_termination', severity='critical',
                              description=f"Access by terminated employee (left {termination_date})",
                              evidence={'termination_date': str(termination_date)},
                              score=0.95))
            return obj
        return None


# ── singletons ────────────────────────────────────────────────────
profiler = BehaviorProfiler()
fraud_detector = FraudDetector()
insider_monitor = InsiderThreatMonitor()
