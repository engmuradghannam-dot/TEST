"""Workflow State Machine with retry & rollback.

Executes parsed BPMN/workflow specs: tracks current node per instance,
evaluates guards on transitions, runs service-task handlers with
configurable retry, and supports compensating rollback of executed steps.
"""
import logging
import time

from .guards import evaluate_guards

logger = logging.getLogger(__name__)


class TransitionDenied(Exception):
    def __init__(self, reasons):
        self.reasons = reasons
        super().__init__("; ".join(reasons))


class StateMachine:
    def __init__(self, spec: dict, handlers: dict | None = None,
                 max_retries: int = 3, retry_backoff: float = 1.5):
        self.spec = spec
        self.nodes = {n["id"]: n for n in spec["nodes"]}
        self.flows_by_source = {}
        for f in spec["flows"]:
            self.flows_by_source.setdefault(f["source"], []).append(f)
        self.handlers = handlers or {}       # node_id -> callable(context) -> result
        self.compensators = {}               # node_id -> callable(context) for rollback
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

    def register_handler(self, node_id, fn, compensator=None):
        self.handlers[node_id] = fn
        if compensator:
            self.compensators[node_id] = compensator

    def initial_node(self) -> str:
        return next(n["id"] for n in self.spec["nodes"] if n["type"] == "start")

    def available_transitions(self, current: str, user, context: dict) -> list[dict]:
        out = []
        for flow in self.flows_by_source.get(current, []):
            guards = flow.get("guards", [])
            ok, _ = evaluate_guards(guards, user, context) if guards else (True, [])
            if ok and self._condition_ok(flow, context):
                out.append(flow)
        return out

    def _condition_ok(self, flow, context) -> bool:
        cond = flow.get("condition")
        if not cond:
            return True
        # condition format: "field <op> value" evaluated by guards.condition_guard
        from .guards import condition_guard
        try:
            field, op, value = cond.split(None, 2)
            try:
                import json as _json
                value = _json.loads(value)
            except Exception:
                pass
            ok, _ = condition_guard(None, context, {"field": field, "op": op, "value": value})
            return ok
        except Exception:
            logger.warning("unparseable condition %r - denying flow", cond)
            return False

    def advance(self, instance, user, context: dict, target: str | None = None) -> str:
        """Move instance forward one node. Executes service tasks with retry;
        rolls back executed steps in this call if a later step fails."""
        current = instance.current_node
        candidates = self.available_transitions(current, user, context)
        if not candidates:
            raise TransitionDenied(["no allowed transitions from " + current])
        if target:
            candidates = [f for f in candidates if f["target"] == target]
            if not candidates:
                raise TransitionDenied([f"transition to {target} not allowed"])

        flow = candidates[0]
        executed = []
        node = self.nodes[flow["target"]]
        try:
            if node["type"] == "service_task":
                self._run_with_retry(node["id"], context)
                executed.append(node["id"])
            instance.current_node = node["id"]
            instance.save(update_fields=["current_node"])
            logger.info("workflow %s advanced %s -> %s",
                        getattr(instance, "pk", "?"), current, node["id"])
            return node["id"]
        except Exception:
            self._rollback(executed, context)
            raise

    def _run_with_retry(self, node_id: str, context: dict):
        fn = self.handlers.get(node_id)
        if fn is None:
            logger.warning("no handler for service task %s - skipping", node_id)
            return
        delay = 1.0
        for attempt in range(1, self.max_retries + 1):
            try:
                return fn(context)
            except Exception as exc:  # noqa: BLE001
                if attempt == self.max_retries:
                    raise
                logger.warning("service task %s attempt %s failed: %s - retrying in %.1fs",
                               node_id, attempt, exc, delay)
                time.sleep(delay)
                delay *= self.retry_backoff

    def _rollback(self, executed: list[str], context: dict):
        for node_id in reversed(executed):
            comp = self.compensators.get(node_id)
            if comp:
                try:
                    comp(context)
                    logger.info("compensated node %s", node_id)
                except Exception as exc:  # noqa: BLE001
                    logger.error("compensation for %s failed: %s", node_id, exc)
