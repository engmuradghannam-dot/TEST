"""Privileged Access Management service + role mining."""
from collections import Counter
from itertools import combinations

from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import PrivilegedSession, RoleMiningReport


def request_elevation(user, role: str, justification: str,
                      duration_minutes: int = 60) -> PrivilegedSession:
    return PrivilegedSession.objects.create(
        user=user, role_requested=role, justification=justification,
        max_duration_minutes=min(duration_minutes, 240))


def active_privileges(user) -> set:
    now = timezone.now()
    return set(PrivilegedSession.objects.filter(
        user=user, status='active', expires_at__gt=now,
    ).values_list('role_requested', flat=True))


def expire_stale_sessions() -> int:
    """Celery-beat task target."""
    return PrivilegedSession.objects.filter(
        status='active', expires_at__lte=timezone.now(),
    ).update(status='expired')


def mine_roles(min_support: int = 2) -> RoleMiningReport:
    """Role Mining: find permission sets shared by >= min_support users and
    propose them as named roles (reduces direct-permission sprawl)."""
    User = get_user_model()
    user_perms = {}
    for u in User.objects.prefetch_related('user_permissions', 'groups'):
        perms = set(u.user_permissions.values_list('codename', flat=True))
        perms |= set(u.groups.values_list('permissions__codename', flat=True))
        perms.discard(None)
        if perms:
            user_perms[u.pk] = frozenset(perms)

    counter = Counter(user_perms.values())
    suggestions = []
    for perm_set, support in counter.most_common():
        if support >= min_support and len(perm_set) >= 2:
            suggestions.append({
                'suggested_role': f'mined_role_{len(suggestions) + 1}',
                'permissions': sorted(perm_set),
                'user_count': support,
            })
    # pairwise overlaps between the largest sets (partial-role hints)
    for a, b in combinations(list(counter)[:10], 2):
        overlap = a & b
        if len(overlap) >= 3:
            suggestions.append({
                'suggested_role': 'shared_' + '_'.join(sorted(overlap)[:2]),
                'permissions': sorted(overlap),
                'user_count': counter[a] + counter[b],
                'type': 'overlap',
            })
    return RoleMiningReport.objects.create(
        suggestions=suggestions[:50], users_analyzed=len(user_perms))
