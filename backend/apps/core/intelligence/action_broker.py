"""Action Broker — the isolation layer between intelligence and execution.

Design rule enforced here:
  AI Brain / Agents / Plugins NEVER mutate domain state directly.
  They emit ProposedAction objects; the broker validates (guards,
  permissions, tenant scope, risk tier) and only then dispatches to a
  registered executor. Every decision is audited and event-emitted.

Risk tiers:
  READ      -> auto-execute
  LOW       -> auto-execute, audited
  MEDIUM    -> requires an allowed role on the acting user
  HIGH      -> requires explicit human approval record before execution
"""
import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional

from django.utils import timezone

from apps.core.runtime.event_bus import event_bus, DomainEvent

logger = logging.getLogger(__name__)


class RiskTier(Enum):
    READ = "read"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ActionStatus(Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    EXECUTED = "executed"
    REJECTED = "rejected"
    FAILED = "failed"


@dataclass
class ProposedAction:
    """What intelligence is allowed to produce: a proposal, not an effect."""
    action_type: str                       # e.g. "inventory.adjust_stock"
    payload: Dict[str, Any]
    tenant_id: str
    proposed_by: str                       # agent/plugin/model identifier
    risk: RiskTier = RiskTier.MEDIUM
    reason: str = ""
    action_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: ActionStatus = ActionStatus.PROPOSED


@dataclass
class ExecutorSpec:
    fn: Callable[[ProposedAction], Any]
    risk: RiskTier
    allowed_roles: tuple = ()              # for MEDIUM tier


class ActionBroker:
    """Single sanctioned bridge: intelligence -> (broker) -> domain."""

    def __init__(self):
        self._executors: Dict[str, ExecutorSpec] = {}
        self._pending_high: Dict[str, ProposedAction] = {}

    # ── registration (domain side) ────────────────────────────────
    def register(self, action_type: str, risk: RiskTier = RiskTier.MEDIUM,
                 allowed_roles: tuple = ()):
        def deco(fn):
            self._executors[action_type] = ExecutorSpec(fn, risk, allowed_roles)
            return fn
        return deco

    # ── submission (intelligence side) ────────────────────────────
    def submit(self, action: ProposedAction, acting_user=None) -> Dict[str, Any]:
        spec = self._executors.get(action.action_type)
        if spec is None:
            return self._reject(action, f"no executor for {action.action_type}")

        # broker's risk assessment overrides the proposer's optimism
        effective_risk = max(action.risk, spec.risk, key=lambda r: list(RiskTier).index(r))

        if not action.tenant_id:
            return self._reject(action, "missing tenant scope")

        if effective_risk in (RiskTier.READ, RiskTier.LOW):
            return self._execute(action)

        if effective_risk is RiskTier.MEDIUM:
            if acting_user is None:
                return self._reject(action, "medium-risk action requires an acting user")
            user_roles = set(acting_user.groups.values_list("name", flat=True))
            if spec.allowed_roles and not (user_roles & set(spec.allowed_roles)):
                return self._reject(
                    action, f"user lacks required role {spec.allowed_roles}")
            return self._execute(action, acting_user)

        # HIGH: park for human approval
        self._pending_high[action.action_id] = action
        self._emit(action, "action.pending_approval")
        logger.info("action %s (%s) parked for approval",
                    action.action_id, action.action_type)
        return {"status": ActionStatus.PROPOSED.value,
                "action_id": action.action_id,
                "message": "awaiting human approval"}

    # ── human approval (management side) ──────────────────────────
    def approve(self, action_id: str, approver) -> Dict[str, Any]:
        action = self._pending_high.pop(action_id, None)
        if action is None:
            raise KeyError(f"no pending action {action_id}")
        if not (approver.is_staff or approver.has_perm("core.approve_ai_action")):
            self._pending_high[action_id] = action
            raise PermissionError("approver lacks core.approve_ai_action")
        action.status = ActionStatus.APPROVED
        self._emit(action, "action.approved", approver_id=str(approver.pk))
        return self._execute(action, approver)

    def reject(self, action_id: str, approver, reason: str = "") -> Dict[str, Any]:
        action = self._pending_high.pop(action_id, None)
        if action is None:
            raise KeyError(f"no pending action {action_id}")
        return self._reject(action, reason or "rejected by approver",
                            approver_id=str(approver.pk))

    def pending(self, tenant_id: str | None = None) -> list:
        acts = self._pending_high.values()
        if tenant_id:
            acts = [a for a in acts if a.tenant_id == tenant_id]
        return [vars(a) for a in acts]

    # ── internals ─────────────────────────────────────────────────
    def _execute(self, action: ProposedAction, user=None) -> Dict[str, Any]:
        spec = self._executors[action.action_type]
        try:
            result = spec.fn(action)
            action.status = ActionStatus.EXECUTED
            self._emit(action, "action.executed",
                       user_id=str(getattr(user, "pk", "")) if user else "")
            self._audit(action, user, ok=True)
            return {"status": action.status.value,
                    "action_id": action.action_id, "result": result}
        except Exception as exc:  # noqa: BLE001
            action.status = ActionStatus.FAILED
            self._emit(action, "action.failed", error=str(exc))
            self._audit(action, user, ok=False, error=str(exc))
            logger.exception("action %s failed", action.action_id)
            return {"status": action.status.value,
                    "action_id": action.action_id, "error": str(exc)}

    def _reject(self, action: ProposedAction, reason: str, **extra) -> Dict[str, Any]:
        action.status = ActionStatus.REJECTED
        self._emit(action, "action.rejected", reason=reason, **extra)
        self._audit(action, None, ok=False, error=reason)
        logger.warning("action %s rejected: %s", action.action_id, reason)
        return {"status": action.status.value,
                "action_id": action.action_id, "reason": reason}

    def _emit(self, action: ProposedAction, event_type: str, **extra):
        try:
            event_bus.publish(DomainEvent.create(
                event_type=event_type, aggregate_type="ai_action",
                aggregate_id=action.action_id, tenant_id=action.tenant_id,
                payload={"action_type": action.action_type,
                         "proposed_by": action.proposed_by,
                         "reason": action.reason, **extra},
            ))
        except Exception:
            logger.warning("event emit failed for action %s", action.action_id)

    def _audit(self, action: ProposedAction, user, ok: bool, error: str = ""):
        try:
            from apps.core.models import AuditLog
            AuditLog.objects.create(
                action=f"ai_action.{action.status.value}",
                model_name=action.action_type,
                object_id=action.action_id,
                changes={"proposed_by": action.proposed_by,
                         "payload": action.payload, "ok": ok, "error": error,
                         "at": timezone.now().isoformat()},
            )
        except Exception:
            logger.debug("audit write skipped for %s", action.action_id)


broker = ActionBroker()
