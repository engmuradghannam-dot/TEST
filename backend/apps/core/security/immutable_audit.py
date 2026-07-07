"""Immutable Audit Trail: hash-chained, digitally signed ledger
(blockchain-style, append-only).

Every record embeds the previous record's hash, so any historical
tampering breaks the chain and is detectable by verify_chain().
Records are HMAC-signed with a server-side key (digital signature);
export_evidence() produces a compliance-evidence bundle.
"""
import hashlib
import hmac
import json

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone


class AuditLedgerEntry(models.Model):
    """Append-only. No update/delete paths are exposed anywhere."""
    sequence = models.BigIntegerField(unique=True, db_index=True)
    event_type = models.CharField(max_length=100, db_index=True)
    payload = models.JSONField()
    recorded_at = models.DateTimeField(default=timezone.now)
    previous_hash = models.CharField(max_length=64)
    entry_hash = models.CharField(max_length=64, unique=True)
    signature = models.CharField(max_length=64)

    class Meta:
        app_label = 'core'
        ordering = ['sequence']

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError('Audit ledger entries are immutable')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('Audit ledger entries cannot be deleted')


GENESIS = '0' * 64


def _canonical(seq, event_type, payload, recorded_at, previous_hash) -> bytes:
    return json.dumps({
        'seq': seq, 'type': event_type, 'payload': payload,
        'at': recorded_at.isoformat(), 'prev': previous_hash,
    }, sort_keys=True, default=str).encode()


def _sign(digest: str) -> str:
    key = getattr(settings, 'AUDIT_SIGNING_KEY', settings.SECRET_KEY)
    return hmac.new(key.encode(), digest.encode(), hashlib.sha256).hexdigest()


class Ledger:
    @transaction.atomic
    def append(self, event_type: str, payload: dict) -> AuditLedgerEntry:
        last = (AuditLedgerEntry.objects
                .select_for_update().order_by('-sequence').first())
        seq = (last.sequence + 1) if last else 1
        prev = last.entry_hash if last else GENESIS
        now = timezone.now()
        digest = hashlib.sha256(
            _canonical(seq, event_type, payload, now, prev)).hexdigest()
        return AuditLedgerEntry.objects.create(
            sequence=seq, event_type=event_type, payload=payload,
            recorded_at=now, previous_hash=prev,
            entry_hash=digest, signature=_sign(digest))

    def verify_chain(self, start: int = 1, end: int | None = None) -> dict:
        qs = AuditLedgerEntry.objects.filter(sequence__gte=start)
        if end:
            qs = qs.filter(sequence__lte=end)
        prev = GENESIS if start == 1 else (
            AuditLedgerEntry.objects.get(sequence=start - 1).entry_hash)
        broken = []
        count = 0
        for e in qs.order_by('sequence').iterator():
            digest = hashlib.sha256(_canonical(
                e.sequence, e.event_type, e.payload,
                e.recorded_at, prev)).hexdigest()
            if digest != e.entry_hash:
                broken.append({'sequence': e.sequence, 'reason': 'hash_mismatch'})
            elif e.previous_hash != prev:
                broken.append({'sequence': e.sequence, 'reason': 'chain_break'})
            elif not hmac.compare_digest(e.signature, _sign(e.entry_hash)):
                broken.append({'sequence': e.sequence, 'reason': 'bad_signature'})
            prev = e.entry_hash
            count += 1
        return {'verified': count, 'intact': not broken, 'broken': broken}

    def export_evidence(self, event_prefix: str = '',
                        since=None) -> dict:
        """Compliance evidence bundle: entries + independent verification."""
        qs = AuditLedgerEntry.objects.all()
        if event_prefix:
            qs = qs.filter(event_type__startswith=event_prefix)
        if since:
            qs = qs.filter(recorded_at__gte=since)
        entries = list(qs.values('sequence', 'event_type', 'payload',
                                 'recorded_at', 'entry_hash', 'signature'))
        return {
            'generated_at': timezone.now().isoformat(),
            'chain_verification': self.verify_chain(),
            'entry_count': len(entries),
            'entries': entries,
        }


ledger = Ledger()
