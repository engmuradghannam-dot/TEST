"""Zero-Trust middleware: verify User + Device + Location + Behavior
on every API request, producing a trust score.

score < DENY_THRESHOLD      -> 403 (blocked, audited)
score < STEPUP_THRESHOLD    -> allowed but flagged for step-up (header),
                               and HIGH-risk write operations are denied
otherwise                   -> allowed

Signals:
- user:     authenticated, active, not locked
- device:   fingerprint known + trusted for this user
- location: IP country vs user's usual countries
- behavior: request hour vs user's usual activity hours; burst rate
"""
import hashlib
import logging
import time

from django.http import JsonResponse

logger = logging.getLogger('nexus.zerotrust')

DENY_THRESHOLD = 0.25
STEPUP_THRESHOLD = 0.55
WRITE_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}
EXEMPT_PREFIXES = ('/api/v1/auth', '/api/auth', '/api/v1/iam/sso',
                   '/admin/login', '/api/health', '/api/v1/core/health')


def fingerprint(request) -> str:
    raw = '|'.join([
        request.META.get('HTTP_USER_AGENT', ''),
        request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
        request.META.get('HTTP_SEC_CH_UA_PLATFORM', ''),
    ])
    return hashlib.sha256(raw.encode()).hexdigest()


def client_ip(request) -> str:
    fwd = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return (fwd.split(',')[0].strip() if fwd
            else request.META.get('REMOTE_ADDR', ''))


class ZeroTrustMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if not path.startswith('/api/') or path.startswith(EXEMPT_PREFIXES):
            return self.get_response(request)
        user = getattr(request, 'user', None)
        if user is None or not user.is_authenticated:
            return self.get_response(request)   # APIAuthMiddleware handles it

        score, signals = self.evaluate(request, user)
        request.trust_score = score
        request.trust_signals = signals

        if score < DENY_THRESHOLD:
            self._audit(user, request, score, signals, 'denied')
            return JsonResponse(
                {'error': 'zero_trust_denied',
                 'message': 'Request blocked by Zero-Trust policy.',
                 'signals': signals}, status=403)

        if score < STEPUP_THRESHOLD and request.method in WRITE_METHODS:
            self._audit(user, request, score, signals, 'stepup_required')
            return JsonResponse(
                {'error': 'step_up_required',
                 'message': 'Additional verification required for writes '
                            'from this context.',
                 'signals': signals}, status=401)

        response = self.get_response(request)
        response['X-Trust-Score'] = f'{score:.2f}'
        return response

    # ── scoring ───────────────────────────────────────────────────
    def evaluate(self, request, user):
        signals = {}
        score = 1.0

        # user signal
        if not user.is_active:
            return 0.0, {'user': 'inactive'}
        signals['user'] = 'ok'

        # device signal
        try:
            from apps.iam.models import DeviceFingerprint
            fp = fingerprint(request)
            device, created = DeviceFingerprint.objects.get_or_create(
                user=user, fingerprint=fp,
                defaults={'user_agent':
                          request.META.get('HTTP_USER_AGENT', '')[:500]})
            if created:
                score -= 0.30
                signals['device'] = 'unknown'
            elif not device.is_trusted:
                score -= 0.15
                signals['device'] = 'known_untrusted'
            else:
                signals['device'] = 'trusted'
        except Exception:
            signals['device'] = 'unavailable'

        # location signal
        try:
            from apps.iam.models import LoginContext
            ip = client_ip(request)
            country = request.META.get('HTTP_CF_IPCOUNTRY',
                                       request.META.get('HTTP_X_COUNTRY', ''))
            usual = set(LoginContext.objects.filter(
                user=user, succeeded=True,
            ).exclude(country='').values_list('country', flat=True)[:200])
            if country and usual and country not in usual:
                score -= 0.25
                signals['location'] = f'new_country:{country}'
            else:
                signals['location'] = 'ok'
            signals['ip'] = ip
        except Exception:
            signals['location'] = 'unavailable'

        # behavior signal: unusual hour + burst detection
        try:
            from django.core.cache import cache
            import datetime
            hour = datetime.datetime.now().hour
            from apps.iam.models import LoginContext
            hours = list(LoginContext.objects.filter(
                user=user, succeeded=True,
            ).values_list('hour_of_day', flat=True)[:500])
            if hours:
                usual_hours = {h for h in hours if hours.count(h) >= 2}
                if usual_hours and hour not in usual_hours and \
                        min(abs(hour - h) for h in usual_hours) > 3:
                    score -= 0.15
                    signals['behavior'] = f'unusual_hour:{hour}'
                else:
                    signals['behavior'] = 'ok'
            else:
                signals['behavior'] = 'no_baseline'
            # burst: > 120 requests / 10s from one user
            key = f'zt:burst:{user.pk}:{int(time.time() // 10)}'
            n = cache.get(key, 0) + 1
            cache.set(key, n, 20)
            if n > 120:
                score -= 0.35
                signals['burst'] = n
        except Exception:
            signals['behavior'] = 'unavailable'

        return max(score, 0.0), signals

    def _audit(self, user, request, score, signals, outcome):
        logger.warning('zero-trust %s user=%s path=%s score=%.2f signals=%s',
                       outcome, user.pk, request.path, score, signals)
        try:
            from apps.core.security.immutable_audit import ledger
            ledger.append('zero_trust.' + outcome, {
                'user_id': str(user.pk), 'path': request.path,
                'score': round(score, 3), 'signals': signals,
            })
        except Exception:
            pass
