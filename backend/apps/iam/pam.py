"""Privileged Access Management helpers using ElevationRequest
for user-level role elevation and RoleMiningJob for role mining."""
from collections import Counter
from itertools import combinations

from django.contrib.auth import get_user_model
from django.utils import timezone


def request_elevation(user, role: str, justification: str,
                      duration_minutes: int = 60):
    from apps.iam.models import ElevationRequest
    return ElevationRequest.objects.create(
        user=user, role_requested=role,
        justification=justification,
        requested_duration_hours=max(1, duration_minutes // 60),
        status='pending',
    )


def approve_elevation(session, approver):
    if session.user_id == approver.pk:
        raise ValueError('Self-approval is not allowed')
    session.status = 'approved'
    session.approved_by = approver
    session.approved_at = timezone.now()
    session.expires_at = (
        session.approved_at
        + timezone.timedelta(hours=session.requested_duration_hours))
    session.save()
    return session


def active_privileges(user) -> set:
    from apps.iam.models import ElevationRequest
    now = timezone.now()
    rows = ElevationRequest.objects.filter(
        user=user, status='approved', expires_at__gt=now,
    ).values_list('role_requested', flat=True)
    return set(rows)


def expire_stale_sessions() -> int:
    from apps.iam.models import ElevationRequest
    return ElevationRequest.objects.filter(
        status='approved', expires_at__lte=timezone.now(),
    ).update(status='expired')


def mine_roles(min_support: int = 2):
    from apps.iam.models import RoleMiningJob
    User = get_user_model()
    user_perms = {}
    for u in User.objects.prefetch_related('user_permissions', 'groups')[:2000]:
        perms = set(u.user_permissions.values_list('codename', flat=True))
        perms |= set(u.groups.values_list('permissions__codename', flat=True))
        perms.discard(None)
        if perms:
            user_perms[u.pk] = frozenset(perms)

    counter = Counter(user_perms.values())
    suggestions = []
    for perm_set, support in counter.most_common():
        if support >= min_support and len(perm_set) >= 2:
            suggestions.append({'suggested_role': f'mined_{len(suggestions)+1}',
                                 'permissions': sorted(perm_set),
                                 'user_count': support})
    for a, b in combinations(list(counter)[:10], 2):
        overlap = a & b
        if len(overlap) >= 3:
            suggestions.append({'suggested_role': 'shared_perm_set',
                                 'permissions': sorted(overlap),
                                 'user_count': counter[a] + counter[b]})

    return RoleMiningJob.objects.create(
        name=f'auto-mine-{timezone.now().date()}',
        company_id=1,  # platform admin company (fallback)
        analysis_type='permission_clustering',
        status='completed',
        users_analyzed=len(user_perms),
        permissions_analyzed=sum(len(p) for p in user_perms.values()),
        roles_suggested=len(suggestions),
        suggested_roles=suggestions[:50],
        started_at=timezone.now(),
        completed_at=timezone.now(),
    )
