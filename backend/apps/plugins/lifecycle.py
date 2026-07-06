"""Plugin lifecycle: Install → Activate → Update → Deactivate → Uninstall.

State machine over the Plugin model with hook dispatch and event emission.
Illegal transitions raise; every step is audit-logged and emitted on the bus.
"""
import logging

from django.db import transaction
from django.utils import timezone

from apps.core.event_bus import bus
from .dependency_resolver import resolve_install_order, DependencyError

logger = logging.getLogger(__name__)

VALID_TRANSITIONS = {
    "registered": {"installed"},
    "installed": {"active", "uninstalled"},
    "active": {"inactive", "updating"},
    "updating": {"active", "inactive"},
    "inactive": {"active", "uninstalled"},
    "uninstalled": set(),
}


class LifecycleError(Exception):
    pass


class PluginLifecycle:
    def __init__(self, plugin):
        self.plugin = plugin

    def _transition(self, new_status: str, event: str, **payload):
        current = self.plugin.status
        if new_status not in VALID_TRANSITIONS.get(current, set()):
            raise LifecycleError(f"illegal transition {current} -> {new_status}")
        with transaction.atomic():
            self.plugin.status = new_status
            self.plugin.status_changed_at = timezone.now()
            self.plugin.save(update_fields=["status", "status_changed_at"])
        bus.emit(f"plugin.{event}", {"plugin": self.plugin.slug,
                                     "version": self.plugin.version, **payload},
                 company_id=getattr(self.plugin, "company_id", None))
        logger.info("plugin %s: %s -> %s", self.plugin.slug, current, new_status)

    def install(self, all_installed: dict):
        graph = {**all_installed,
                 self.plugin.slug: {"version": self.plugin.version,
                                    "requires": self.plugin.requires or {}}}
        try:
            resolve_install_order(graph)
        except DependencyError as exc:
            raise LifecycleError(str(exc)) from exc
        self._run_hook("on_install")
        self._transition("installed", "installed")

    def activate(self):
        self._run_hook("on_activate")
        self._transition("active", "activated")

    def update(self, new_version: str):
        self._transition("updating", "update_started", to_version=new_version)
        try:
            self._run_hook("on_update")
            self.plugin.version = new_version
            self.plugin.save(update_fields=["version"])
            self._transition("active", "updated", version=new_version)
        except Exception:
            self._transition("inactive", "update_failed")
            raise

    def deactivate(self):
        self._run_hook("on_deactivate")
        self._transition("inactive", "deactivated")

    def uninstall(self, all_installed: dict):
        dependents = [name for name, meta in all_installed.items()
                      if self.plugin.slug in (meta.get("requires") or {})]
        if dependents:
            raise LifecycleError(
                f"cannot uninstall: required by {', '.join(dependents)}")
        self._run_hook("on_uninstall")
        self._transition("uninstalled", "uninstalled")

    def _run_hook(self, hook_name: str):
        hooks = getattr(self.plugin, "hooks", None) or {}
        code = hooks.get(hook_name)
        if code:
            from .sandbox import run_sandboxed
            run_sandboxed(code, {"plugin": self.plugin.slug}, timeout_seconds=10)
