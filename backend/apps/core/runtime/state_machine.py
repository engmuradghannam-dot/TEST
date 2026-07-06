"""
Generic State Machine Engine for Nexus CE-ERP OS
Supports: state transitions, validation guards, audit trail, event-driven transitions
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from apps.core.event_bus import event_bus, DomainEvent, EventTypes, EventPriority

logger = logging.getLogger(__name__)


class TransitionGuard:
    """Base class for transition validation guards"""

    def check(self, instance, from_state: str, to_state: str, user=None, context: Dict = None) -> Tuple[bool, Optional[str]]:
        """Returns (is_allowed, error_message)"""
        raise NotImplementedError


class PermissionGuard(TransitionGuard):
    """Guard that checks user permissions"""

    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions

    def check(self, instance, from_state: str, to_state: str, user=None, context: Dict = None):
        if not user:
            return False, "User authentication required"
        user_perms = set(user.user_permissions.values_list('codename', flat=True))
        if not set(self.required_permissions).issubset(user_perms):
            missing = set(self.required_permissions) - user_perms
            return False, f"Missing permissions: {', '.join(missing)}"
        return True, None


class RoleGuard(TransitionGuard):
    """Guard that checks user roles"""

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def check(self, instance, from_state: str, to_state: str, user=None, context: Dict = None):
        if not user:
            return False, "User authentication required"
        if user.role not in self.allowed_roles:
            return False, f"Role '{user.role}' not allowed. Required: {', '.join(self.allowed_roles)}"
        return True, None


class ConditionGuard(TransitionGuard):
    """Guard that checks a custom condition"""

    def __init__(self, condition_fn: Callable, error_message: str = "Condition not met"):
        self.condition_fn = condition_fn
        self.error_message = error_message

    def check(self, instance, from_state: str, to_state: str, user=None, context: Dict = None):
        ctx = context or {}
        ctx['user'] = user
        ctx['instance'] = instance
        if self.condition_fn(ctx):
            return True, None
        return False, self.error_message


class AmountGuard(TransitionGuard):
    """Guard for amount-based transitions (e.g., invoice approval thresholds)"""

    def __init__(self, max_amount: float, amount_field: str = 'total_amount'):
        self.max_amount = max_amount
        self.amount_field = amount_field

    def check(self, instance, from_state: str, to_state: str, user=None, context: Dict = None):
        amount = getattr(instance, self.amount_field, 0)
        if amount > self.max_amount:
            return False, f"Amount {amount} exceeds maximum {self.max_amount} for this transition"
        return True, None


@dataclass
class StateTransition:
    """Defines a valid state transition"""
    from_state: str
    to_state: str
    action: str
    guards: List[TransitionGuard] = field(default_factory=list)
    side_effects: List[Callable] = field(default_factory=list)
    requires_approval: bool = False
    approval_workflow_id: Optional[str] = None
    auto_transition: bool = False
    auto_condition: Optional[Callable] = None
    timeout_hours: Optional[int] = None


class StateMachineDefinition:
    """Defines a complete state machine for a document type"""

    def __init__(self, name: str, initial_state: str, states: List[str]):
        self.name = name
        self.initial_state = initial_state
        self.states = set(states)
        self.transitions: Dict[str, List[StateTransition]] = {}
        self._transitions_by_action: Dict[str, StateTransition] = {}
        self.final_states: Set[str] = set()

    def add_transition(self, transition: StateTransition):
        key = f"{transition.from_state}->{transition.to_state}"
        self.transitions.setdefault(transition.from_state, []).append(transition)
        self._transitions_by_action[transition.action] = transition

    def get_transitions_from(self, state: str) -> List[StateTransition]:
        return self.transitions.get(state, [])

    def get_transition(self, from_state: str, action: str) -> Optional[StateTransition]:
        for t in self.transitions.get(from_state, []):
            if t.action == action:
                return t
        return None

    def can_transition(self, from_state: str, to_state: str) -> bool:
        for t in self.transitions.get(from_state, []):
            if t.to_state == to_state:
                return True
        return False

    def set_final_states(self, states: List[str]):
        self.final_states = set(states)


class StateMachineRegistry:
    """Registry of all state machine definitions"""

    _registry: Dict[str, StateMachineDefinition] = {}

    @classmethod
    def register(cls, document_type: str, definition: StateMachineDefinition):
        cls._registry[document_type] = definition
        logger.info(f"State machine registered for {document_type}")

    @classmethod
    def get(cls, document_type: str) -> Optional[StateMachineDefinition]:
        return cls._registry.get(document_type)

    @classmethod
    def list_document_types(cls) -> List[str]:
        return list(cls._registry.keys())


# ============================================================
# State Machine Model
# ============================================================

class StateMachineInstance(models.Model):
    """Tracks state machine execution for a specific document instance"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_type = models.CharField(max_length=100)
    document_id = models.CharField(max_length=100)
    tenant_id = models.CharField(max_length=100)
    current_state = models.CharField(max_length=100)
    previous_state = models.CharField(max_length=100, blank=True)
    state_data = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['document_type', 'document_id', 'tenant_id']),
            models.Index(fields=['current_state', 'is_active']),
        ]

    def __str__(self):
        return f"{self.document_type}#{self.document_id} -> {self.current_state}"


class StateTransitionLog(models.Model):
    """Audit trail for every state transition"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state_machine = models.ForeignKey(StateMachineInstance, on_delete=models.CASCADE, related_name='transition_logs')
    from_state = models.CharField(max_length=100)
    to_state = models.CharField(max_length=100)
    action = models.CharField(max_length=100)
    triggered_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)
    triggered_by_role = models.CharField(max_length=50, blank=True)
    context = models.JSONField(default=dict, blank=True)
    guard_results = models.JSONField(default=dict, blank=True)
    side_effects_executed = models.JSONField(default=list, blank=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['state_machine', 'created_at']),
        ]

    def __str__(self):
        return f"{self.from_state} -> {self.to_state} ({self.action})"


# ============================================================
# State Machine Executor
# ============================================================

class StateMachineExecutor:
    """Executes state transitions with guards, side effects, and event publishing"""

    def __init__(self, definition: StateMachineDefinition):
        self.definition = definition

    @transaction.atomic
    def transition(self, instance: StateMachineInstance, action: str, 
                   user=None, context: Dict = None, force: bool = False) -> Tuple[bool, str, Optional[StateTransitionLog]]:
        """Execute a state transition"""
        context = context or {}

        # Find transition
        transition_def = self.definition.get_transition(instance.current_state, action)
        if not transition_def:
            return False, f"Invalid action '{action}' from state '{instance.current_state}'", None

        # Run guards (unless forced)
        guard_results = {}
        if not force:
            for guard in transition_def.guards:
                allowed, error = guard.check(instance, instance.current_state, transition_def.to_state, user, context)
                guard_results[guard.__class__.__name__] = {'allowed': allowed, 'error': error}
                if not allowed:
                    log = StateTransitionLog.objects.create(
                        state_machine=instance,
                        from_state=instance.current_state,
                        to_state=transition_def.to_state,
                        action=action,
                        triggered_by=user,
                        triggered_by_role=getattr(user, 'role', ''),
                        context=context,
                        guard_results=guard_results,
                        success=False,
                        error_message=error
                    )
                    return False, error, log

        # Execute side effects
        side_effects_results = []
        for effect in transition_def.side_effects:
            try:
                effect(instance, context)
                side_effects_results.append({'effect': effect.__name__, 'status': 'success'})
            except Exception as e:
                side_effects_results.append({'effect': effect.__name__, 'status': 'failed', 'error': str(e)})
                logger.error(f"Side effect failed: {e}")

        # Update state
        instance.previous_state = instance.current_state
        instance.current_state = transition_def.to_state
        instance.state_data.update(context.get('state_data', {}))

        if transition_def.to_state in self.definition.final_states:
            instance.is_active = False
            instance.completed_at = datetime.now()

        instance.save()

        # Create audit log
        log = StateTransitionLog.objects.create(
            state_machine=instance,
            from_state=instance.previous_state,
            to_state=transition_def.to_state,
            action=action,
            triggered_by=user,
            triggered_by_role=getattr(user, 'role', ''),
            context=context,
            guard_results=guard_results,
            side_effects_executed=side_effects_results,
            success=True
        )

        # Publish event
        event = DomainEvent.create(
            event_type=EventTypes.STATE_TRANSITIONED,
            aggregate_type=instance.document_type,
            aggregate_id=instance.document_id,
            tenant_id=instance.tenant_id,
            payload={
                'from_state': instance.previous_state,
                'to_state': transition_def.to_state,
                'action': action,
                'user_id': str(user.id) if user else None,
                'guard_results': guard_results,
                'side_effects': side_effects_results
            },
            priority=EventPriority.HIGH
        )
        event_bus.publish(event)

        logger.info(f"State transition: {instance.document_type}#{instance.document_id} {instance.previous_state} -> {transition_def.to_state}")
        return True, f"Transitioned to {transition_def.to_state}", log

    def get_available_actions(self, instance: StateMachineInstance, user=None, context: Dict = None) -> List[Dict]:
        """Get list of available actions from current state"""
        transitions = self.definition.get_transitions_from(instance.current_state)
        available = []
        for t in transitions:
            allowed = True
            errors = []
            for guard in t.guards:
                ok, err = guard.check(instance, instance.current_state, t.to_state, user, context)
                if not ok:
                    allowed = False
                    errors.append(err)
            available.append({
                'action': t.action,
                'to_state': t.to_state,
                'allowed': allowed,
                'errors': errors,
                'requires_approval': t.requires_approval,
                'auto_transition': t.auto_transition
            })
        return available

    def auto_transition(self, instance: StateMachineInstance, context: Dict = None) -> Optional[StateTransitionLog]:
        """Check and execute auto-transitions"""
        transitions = self.definition.get_transitions_from(instance.current_state)
        for t in transitions:
            if t.auto_transition and t.auto_condition:
                if t.auto_condition(context or {}):
                    success, msg, log = self.transition(instance, t.action, context=context)
                    if success:
                        return log
        return None


# ============================================================
# Pre-built State Machines
# ============================================================

def register_invoice_state_machine():
    """Invoice state machine with approval thresholds"""
    sm = StateMachineDefinition(
        name="Invoice State Machine",
        initial_state="draft",
        states=["draft", "pending_approval", "approved", "sent", "paid", "overdue", "cancelled", "write_off"]
    )

    sm.add_transition(StateTransition("draft", "pending_approval", "submit", guards=[
        RoleGuard(["User", "Manager", "Admin", "Accountant"])
    ]))
    sm.add_transition(StateTransition("pending_approval", "approved", "approve", guards=[
        RoleGuard(["Manager", "Admin"]),
        AmountGuard(10000, "total_amount")
    ]))
    sm.add_transition(StateTransition("pending_approval", "draft", "reject", guards=[
        RoleGuard(["Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("approved", "sent", "send", guards=[
        RoleGuard(["Accountant", "Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("sent", "paid", "mark_paid", guards=[
        RoleGuard(["Accountant", "Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("sent", "overdue", "mark_overdue", auto_transition=True))
    sm.add_transition(StateTransition("overdue", "paid", "mark_paid", guards=[
        RoleGuard(["Accountant", "Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("draft", "cancelled", "cancel", guards=[
        RoleGuard(["Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("pending_approval", "cancelled", "cancel", guards=[
        RoleGuard(["Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("overdue", "write_off", "write_off", guards=[
        RoleGuard(["Admin"])
    ]))

    sm.set_final_states(["paid", "cancelled", "write_off"])
    StateMachineRegistry.register("invoice", sm)


def register_purchase_order_state_machine():
    """Purchase Order state machine"""
    sm = StateMachineDefinition(
        name="Purchase Order State Machine",
        initial_state="draft",
        states=["draft", "pending_approval", "approved", "sent_to_supplier", "partially_received", 
                "received", "cancelled", "closed"]
    )

    sm.add_transition(StateTransition("draft", "pending_approval", "submit", guards=[
        RoleGuard(["User", "Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("pending_approval", "approved", "approve", guards=[
        RoleGuard(["Manager", "Admin"]),
        AmountGuard(50000, "total_amount")
    ]))
    sm.add_transition(StateTransition("pending_approval", "draft", "reject", guards=[
        RoleGuard(["Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("approved", "sent_to_supplier", "send", guards=[
        RoleGuard(["Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("sent_to_supplier", "partially_received", "partial_receive", guards=[
        RoleGuard(["Manager", "Admin", "Inventory"])
    ]))
    sm.add_transition(StateTransition("sent_to_supplier", "received", "receive", guards=[
        RoleGuard(["Manager", "Admin", "Inventory"])
    ]))
    sm.add_transition(StateTransition("partially_received", "received", "complete", guards=[
        RoleGuard(["Manager", "Admin", "Inventory"])
    ]))
    sm.add_transition(StateTransition("received", "closed", "close", guards=[
        RoleGuard(["Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("draft", "cancelled", "cancel", guards=[
        RoleGuard(["Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("pending_approval", "cancelled", "cancel", guards=[
        RoleGuard(["Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("approved", "cancelled", "cancel", guards=[
        RoleGuard(["Admin"])
    ]))

    sm.set_final_states(["closed", "cancelled"])
    StateMachineRegistry.register("purchase_order", sm)


def register_sales_order_state_machine():
    """Sales Order state machine"""
    sm = StateMachineDefinition(
        name="Sales Order State Machine",
        initial_state="draft",
        states=["draft", "confirmed", "processing", "shipped", "delivered", "invoiced", "paid", "cancelled", "returned"]
    )

    sm.add_transition(StateTransition("draft", "confirmed", "confirm", guards=[
        RoleGuard(["Sales", "Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("confirmed", "processing", "process", guards=[
        RoleGuard(["Manager", "Admin", "Inventory"])
    ]))
    sm.add_transition(StateTransition("processing", "shipped", "ship", guards=[
        RoleGuard(["Manager", "Admin", "Inventory"])
    ]))
    sm.add_transition(StateTransition("shipped", "delivered", "deliver", guards=[
        RoleGuard(["Sales", "Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("delivered", "invoiced", "invoice", guards=[
        RoleGuard(["Accountant", "Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("invoiced", "paid", "mark_paid", guards=[
        RoleGuard(["Accountant", "Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("draft", "cancelled", "cancel", guards=[
        RoleGuard(["Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("confirmed", "cancelled", "cancel", guards=[
        RoleGuard(["Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("delivered", "returned", "return", guards=[
        RoleGuard(["Manager", "Admin"])
    ]))

    sm.set_final_states(["paid", "cancelled", "returned"])
    StateMachineRegistry.register("sales_order", sm)


def register_employee_state_machine():
    """Employee lifecycle state machine"""
    sm = StateMachineDefinition(
        name="Employee State Machine",
        initial_state="applicant",
        states=["applicant", "interviewing", "offered", "hired", "onboarding", 
                "active", "on_leave", "suspended", "terminated", "resigned"]
    )

    sm.add_transition(StateTransition("applicant", "interviewing", "schedule_interview", guards=[
        RoleGuard(["HR", "Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("interviewing", "offered", "make_offer", guards=[
        RoleGuard(["HR", "Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("interviewing", "applicant", "reject", guards=[
        RoleGuard(["HR", "Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("offered", "hired", "accept", guards=[
        RoleGuard(["HR", "Admin"])
    ]))
    sm.add_transition(StateTransition("offered", "applicant", "decline", guards=[
        RoleGuard(["HR", "Admin"])
    ]))
    sm.add_transition(StateTransition("hired", "onboarding", "start_onboarding", guards=[
        RoleGuard(["HR", "Admin"])
    ]))
    sm.add_transition(StateTransition("onboarding", "active", "complete_onboarding", guards=[
        RoleGuard(["HR", "Admin"])
    ]))
    sm.add_transition(StateTransition("active", "on_leave", "request_leave", guards=[
        RoleGuard(["HR", "Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("on_leave", "active", "return_from_leave", guards=[
        RoleGuard(["HR", "Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("active", "suspended", "suspend", guards=[
        RoleGuard(["Manager", "Admin"])
    ]))
    sm.add_transition(StateTransition("suspended", "active", "reinstate", guards=[
        RoleGuard(["Admin"])
    ]))
    sm.add_transition(StateTransition("active", "terminated", "terminate", guards=[
        RoleGuard(["Admin"])
    ]))
    sm.add_transition(StateTransition("active", "resigned", "resign", guards=[
        RoleGuard(["HR", "Admin"])
    ]))

    sm.set_final_states(["terminated", "resigned"])
    StateMachineRegistry.register("employee", sm)


# Register all state machines on module load
register_invoice_state_machine()
register_purchase_order_state_machine()
register_sales_order_state_machine()
register_employee_state_machine()
