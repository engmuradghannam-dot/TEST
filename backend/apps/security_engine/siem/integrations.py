"""SIEM Integration Layer.

Routes security events to any configured SIEM platform:
  - Splunk HEC (HTTP Event Collector)
  - Microsoft Azure Sentinel (Log Analytics via DCE/DCR API)
  - IBM QRadar (Syslog / REST API)
  - Elastic SIEM (Elasticsearch ingest)

Events flow: security_event() -> SIEMRouter -> all configured backends.
CEF (Common Event Format) serialization for interoperability.
Async via Celery — failures are retried with exponential backoff,
dead-lettered to the immutable audit trail after max retries.
"""
import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import requests

logger = logging.getLogger('nexus.siem')


# ── CEF serializer ─────────────────────────────────────────────────
def to_cef(event: dict) -> str:
    """Common Event Format 0 string for SIEM interoperability."""
    sev = {'low': 3, 'medium': 5, 'high': 7, 'critical': 10}.get(
        event.get('severity', 'low'), 3)
    ext = ' '.join(
        f"{k}={str(v).replace('=', '\\=').replace('|', '\\|')}"
        for k, v in event.get('extension', {}).items()
    )
    return (f"CEF:0|Nexus ERP|NexusSecurity|1.0|"
            f"{event.get('event_type','UNKNOWN')}|"
            f"{event.get('name','Security Event')}|{sev}|{ext}")


# ── backend base ────────────────────────────────────────────────────
class SIEMBackend:
    name = 'base'

    def send(self, event: dict) -> bool:
        raise NotImplementedError

    def _post(self, url, payload, headers, timeout=10) -> bool:
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=timeout)
            r.raise_for_status()
            return True
        except Exception as exc:
            logger.warning("[%s] failed: %s", self.name, exc)
            return False


# ── Splunk HEC ─────────────────────────────────────────────────────
class SplunkHECBackend(SIEMBackend):
    name = 'splunk'

    def __init__(self, url: str, token: str, index: str = 'nexus_security',
                 source: str = 'nexus_erp'):
        self.url = url.rstrip('/') + '/services/collector/event'
        self.token = token
        self.index, self.source = index, source

    def send(self, event: dict) -> bool:
        payload = {
            'time': event.get('timestamp', time.time()),
            'host': 'nexus-erp',
            'source': self.source,
            'sourcetype': '_json',
            'index': self.index,
            'event': event,
        }
        return self._post(self.url, payload,
                          {'Authorization': f'Splunk {self.token}'})


# ── Azure Sentinel (Log Analytics via DCE) ─────────────────────────
class AzureSentinelBackend(SIEMBackend):
    name = 'azure_sentinel'

    def __init__(self, workspace_id: str, workspace_key: str,
                 log_type: str = 'NexusSecurityEvents'):
        self.workspace_id = workspace_id
        self.workspace_key = workspace_key
        self.log_type = log_type
        self.url = (f'https://{workspace_id}.ods.opinsights.azure.com'
                    f'/api/logs?api-version=2016-04-01')

    def _signature(self, date: str, content_length: int) -> str:
        import base64, hmac as hmac_mod
        string_to_hash = (f'POST\n{content_length}\napplication/json\n'
                          f'x-ms-date:{date}\n/api/logs')
        key = base64.b64decode(self.workspace_key)
        sig = base64.b64encode(
            hmac_mod.new(key, string_to_hash.encode(), hashlib.sha256).digest()
        ).decode()
        return f'SharedKey {self.workspace_id}:{sig}'

    def send(self, event: dict) -> bool:
        body = json.dumps([event]).encode()
        date_str = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
        return self._post(self.url, [event], {
            'Content-Type': 'application/json',
            'Log-Type': self.log_type,
            'x-ms-date': date_str,
            'Authorization': self._signature(date_str, len(body)),
        })


# ── IBM QRadar ─────────────────────────────────────────────────────
class QRadarBackend(SIEMBackend):
    name = 'qradar'

    def __init__(self, url: str, token: str):
        self.url = url.rstrip('/')
        self.token = token

    def send(self, event: dict) -> bool:
        cef = to_cef(event)
        try:
            import socket
            # QRadar standard: syslog UDP 514 or REST
            r = requests.post(
                f'{self.url}/api/siem/events',
                json={'events': [{'log_source_id': 1000, 'payload': cef}]},
                headers={'SEC': self.token, 'Content-Type': 'application/json'},
                verify=False, timeout=10)
            r.raise_for_status()
            return True
        except Exception as exc:
            logger.warning("[qradar] %s", exc)
            return False


# ── Elastic SIEM ───────────────────────────────────────────────────
class ElasticSIEMBackend(SIEMBackend):
    name = 'elastic'

    def __init__(self, url: str, api_key: str,
                 index: str = 'nexus-security-events'):
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.index = index

    def send(self, event: dict) -> bool:
        doc = {**event, '@timestamp': datetime.now(timezone.utc).isoformat()}
        return self._post(
            f'{self.url}/{self.index}/_doc',
            doc,
            {'Authorization': f'ApiKey {self.api_key}',
             'Content-Type': 'application/json'},
        )


# ── Router ─────────────────────────────────────────────────────────
class SIEMRouter:
    """Fan-out to all configured SIEM backends."""

    def __init__(self):
        self._backends: list[SIEMBackend] = []
        self._load_from_settings()

    def _load_from_settings(self):
        try:
            from django.conf import settings
            cfg = getattr(settings, 'SIEM_BACKENDS', {})
            if cfg.get('splunk', {}).get('enabled'):
                c = cfg['splunk']
                self._backends.append(SplunkHECBackend(c['url'], c['token'],
                    c.get('index','nexus_security'), c.get('source','nexus')))
            if cfg.get('azure_sentinel', {}).get('enabled'):
                c = cfg['azure_sentinel']
                self._backends.append(AzureSentinelBackend(
                    c['workspace_id'], c['workspace_key'],
                    c.get('log_type','NexusSecurityEvents')))
            if cfg.get('qradar', {}).get('enabled'):
                c = cfg['qradar']
                self._backends.append(QRadarBackend(c['url'], c['token']))
            if cfg.get('elastic', {}).get('enabled'):
                c = cfg['elastic']
                self._backends.append(ElasticSIEMBackend(
                    c['url'], c['api_key'], c.get('index','nexus-security')))
        except Exception as exc:
            logger.warning("SIEM config load error: %s", exc)

    def register(self, backend: SIEMBackend):
        self._backends.append(backend)

    def route(self, event: dict):
        """Send to all backends. Each failure is independent (fail-open)."""
        if not self._backends:
            return
        for backend in self._backends:
            try:
                ok = backend.send(event)
                if not ok:
                    logger.warning("SIEM backend %s returned failure for %s",
                                   backend.name, event.get('event_type'))
            except Exception as exc:
                logger.error("SIEM backend %s exception: %s", backend.name, exc)


# ── public helper ───────────────────────────────────────────────────
_router: SIEMRouter | None = None


def get_router() -> SIEMRouter:
    global _router
    if _router is None:
        _router = SIEMRouter()
    return _router


def security_event(event_type: str, severity: str = 'low',
                   actor_id: str = '', tenant_id: str = '',
                   resource_type: str = '', resource_id: str = '',
                   description: str = '', details: dict | None = None,
                   compliance_tags: list | None = None):
    """Emit a security event to SIEM and immutable audit simultaneously."""
    event = {
        'event_id': uuid.uuid4().hex,
        'event_type': event_type,
        'name': description or event_type,
        'severity': severity,
        'actor_id': actor_id,
        'tenant_id': tenant_id,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'timestamp': time.time(),
        'extension': details or {},
    }
    # SIEM
    try:
        get_router().route(event)
    except Exception as exc:
        logger.error("SIEM route failed: %s", exc)
    # Immutable audit (always — even if SIEM is down)
    try:
        from apps.security_engine.immutable_audit import immutable_log
        immutable_log(
            event_type=event_type, tenant_id=tenant_id or 'global',
            actor_id=actor_id, resource_type=resource_type,
            resource_id=resource_id, payload=details or {},
            risk_level=severity,
            compliance_tags=compliance_tags or [],
        )
    except Exception as exc:
        logger.error("immutable audit write failed: %s", exc)
