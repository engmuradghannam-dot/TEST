"""Controlled deployment of approved suggestions with rollback.

Only whitelisted, reversible change types are auto-applicable
(feature flags / config keys stored in DB). Code changes are never
auto-deployed - they stay as human tickets.
"""
import logging

from django.utils import timezone

from apps.core.event_bus import bus
from .models import ImprovementSuggestion

logger = logging.getLogger(__name__)

APPLIERS = {}


def register_applier(change_type):
    def deco(fn):
        APPLIERS[change_type] = fn
        return fn
    return deco


@register_applier("config")
def _apply_config(change: dict) -> dict:
    """change: {"key": ..., "value": ...} against core SystemSetting."""
    from apps.core.models import SystemSetting
    key, value = change["key"], change["value"]
    setting, _ = SystemSetting.objects.get_or_create(key=key)
    snapshot = {"key": key, "value": setting.value}
    setting.value = value
    setting.save(update_fields=["value"])
    return snapshot


class ControlledDeployer:
    def deploy(self, suggestion: ImprovementSuggestion, user):
        if suggestion.status != "approved":
            raise ValueError("only approved suggestions can be deployed")
        change = suggestion.proposed_change or {}
        applier = APPLIERS.get(change.get("type"))
        if applier is None:
            raise ValueError(
                f"change type {change.get('type')!r} is not auto-deployable")
        snapshot = applier(change)
        suggestion.rollback_snapshot = snapshot
        suggestion.status = "deployed"
        suggestion.deployed_at = timezone.now()
        suggestion.save(update_fields=["rollback_snapshot", "status", "deployed_at"])
        bus.emit("self_improvement.deployed",
                 {"suggestion_id": suggestion.pk, "by": user.pk})
        logger.info("deployed suggestion %s by user %s", suggestion.pk, user.pk)

    def rollback(self, suggestion: ImprovementSuggestion, user):
        if suggestion.status != "deployed" or not suggestion.rollback_snapshot:
            raise ValueError("nothing to roll back")
        change = dict(suggestion.proposed_change or {})
        change.update(suggestion.rollback_snapshot)
        APPLIERS[change["type"]](change)
        suggestion.status = "rolled_back"
        suggestion.save(update_fields=["status"])
        bus.emit("self_improvement.rolled_back",
                 {"suggestion_id": suggestion.pk, "by": user.pk})
