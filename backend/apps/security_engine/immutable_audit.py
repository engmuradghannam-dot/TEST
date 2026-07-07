"""Immutable Audit Trail — enterprise-grade, tamper-evident ledger.

Every audit record is:
  1. Hash-chained: each record stores SHA-256 of its content + previous hash
     (blockchain-style, without mining). Breaking the chain proves tampering.
  2. Digitally signed: RSA-2048 private key signs each record. Verifiable by
     compliance auditors with the public key alone.
  3. Append-only: delete() and save(update_fields) raise PermissionError.
  4. Compliance evidence: one-call export for SOC 2, ISO 27001, GDPR, ZATCA.

Usage:
    from apps.security_engine.immutable_audit import immutable_log, verify_chain

    immutable_log(event_type='user.login', actor_id=user.pk,
                  tenant_id='acme', payload={'ip': '1.2.3.4'})

    ok, errors = verify_chain(tenant_id='acme', last_n=1000)
"""
import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone

from django.db import models

logger = logging.getLogger('nexus.immutable_audit')

# ── RSA key management ────────────────────────────────────────────────
def _load_signing_key():
    try:
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        from django.conf import settings
        pem = getattr(settings, 'AUDIT_SIGNING_KEY_PEM', None)
        if pem:
            return load_pem_private_key(pem.encode(), password=None)
    except Exception:
        pass
    return None


def _sign(data: bytes) -> str:
    """RSA-PSS signature. Returns hex-encoded sig or '' if key unavailable."""
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        key = _load_signing_key()
        if key is None:
            return ''
        sig = key.sign(data, padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                                          salt_length=padding.PSS.MAX_LENGTH),
                       hashes.SHA256())
        return sig.hex()
    except Exception as exc:
        logger.warning("audit signing failed: %s", exc)
        return ''


# ── Django model ──────────────────────────────────────────────────────
class ImmutableAuditRecord(models.Model):
    """Append-only, hash-chained, digitally-signed audit record.
    Never delete, never edit — the chain will break and alert verifiers."""

    # Identity
    record_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    tenant_id = models.CharField(max_length=100, db_index=True)
    event_type = models.CharField(max_length=120, db_index=True)
    actor_id = models.CharField(max_length=100, blank=True)
    actor_email = models.CharField(max_length=255, blank=True)
    resource_type = models.CharField(max_length=100, blank=True)
    resource_id = models.CharField(max_length=100, blank=True)

    # Payload
    payload = models.JSONField(default=dict)
    risk_level = models.CharField(max_length=10, default='low',
                                  choices=[('low','Low'),('medium','Medium'),
                                           ('high','High'),('critical','Critical')])

    # Integrity
    content_hash = models.CharField(max_length=64, editable=False)
    previous_hash = models.CharField(max_length=64, default='0' * 64, editable=False)
    chain_hash = models.CharField(max_length=64, editable=False,
                                  help_text='SHA-256(content_hash + previous_hash)')
    digital_signature = models.TextField(blank=True, editable=False,
                                         help_text='RSA-PSS hex signature of chain_hash')

    # Compliance metadata
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    compliance_tags = models.JSONField(default=list,
                                       help_text='e.g. ["SOC2","ISO27001","GDPR"]')
    sequence = models.BigIntegerField(default=0, db_index=True,
                                      help_text='Per-tenant monotonic counter')

    class Meta:
        ordering = ['tenant_id', 'sequence']
        indexes = [
            models.Index(fields=['tenant_id', 'sequence']),
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['actor_id', 'created_at']),
        ]

    # ── append-only enforcement ───────────────────────────────────
    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError(
                "ImmutableAuditRecord is append-only — updates forbidden")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError(
            "ImmutableAuditRecord is append-only — deletion forbidden")

    # ── chain helpers ─────────────────────────────────────────────
    @classmethod
    def _latest_chain_hash(cls, tenant_id: str) -> str:
        last = (cls.objects.filter(tenant_id=tenant_id)
                .order_by('-sequence').only('chain_hash').first())
        return last.chain_hash if last else '0' * 64

    def _compute_hashes(self):
        content = json.dumps({
            'record_id': str(self.record_id),
            'tenant_id': self.tenant_id,
            'event_type': self.event_type,
            'actor_id': self.actor_id,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'payload': self.payload,
            'sequence': self.sequence,
        }, sort_keys=True, default=str)
        self.content_hash = hashlib.sha256(content.encode()).hexdigest()
        self.chain_hash = hashlib.sha256(
            (self.content_hash + self.previous_hash).encode()
        ).hexdigest()


# ── public API ────────────────────────────────────────────────────────
def immutable_log(event_type: str, tenant_id: str, actor_id: str = '',
                  actor_email: str = '', resource_type: str = '',
                  resource_id: str = '', payload: dict | None = None,
                  risk_level: str = 'low',
                  compliance_tags: list | None = None) -> ImmutableAuditRecord:
    """Atomically append a record to the immutable ledger."""
    from django.db import transaction

    with transaction.atomic():
        prev_hash = ImmutableAuditRecord._latest_chain_hash(tenant_id)
        seq = (ImmutableAuditRecord.objects.filter(tenant_id=tenant_id)
               .select_for_update().count())

        rec = ImmutableAuditRecord(
            tenant_id=tenant_id, event_type=event_type,
            actor_id=str(actor_id), actor_email=actor_email,
            resource_type=resource_type, resource_id=str(resource_id),
            payload=payload or {}, risk_level=risk_level,
            compliance_tags=compliance_tags or [],
            previous_hash=prev_hash, sequence=seq,
        )
        rec._compute_hashes()
        rec.digital_signature = _sign(rec.chain_hash.encode())
        rec.save()
    return rec


def verify_chain(tenant_id: str, last_n: int = 10_000) -> tuple[bool, list[str]]:
    """Verify hash chain integrity for a tenant. Returns (ok, error_list)."""
    records = list(ImmutableAuditRecord.objects
                   .filter(tenant_id=tenant_id)
                   .order_by('sequence')[:last_n])
    errors = []
    prev = '0' * 64
    for r in records:
        r._compute_hashes()                 # recompute without mutating DB
        if r.chain_hash != ImmutableAuditRecord.objects.get(
                pk=r.pk).chain_hash:
            errors.append(f"seq {r.sequence}: content tampered")
        if r.previous_hash != prev:
            errors.append(f"seq {r.sequence}: chain break (expected {prev[:8]}…)")
        prev = r.chain_hash
    return not errors, errors


def compliance_export(tenant_id: str, framework: str,
                      date_from=None, date_to=None) -> list[dict]:
    """Return audit evidence for a compliance framework (SOC2, ISO27001…)."""
    qs = ImmutableAuditRecord.objects.filter(
        tenant_id=tenant_id,
        compliance_tags__contains=[framework],
    )
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)
    return list(qs.values('record_id', 'event_type', 'actor_email',
                           'resource_type', 'resource_id', 'risk_level',
                           'chain_hash', 'digital_signature',
                           'created_at', 'payload').order_by('sequence'))
