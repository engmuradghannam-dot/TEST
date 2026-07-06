"""Transition guards: Permission / Role / Condition / Amount.

Each guard evaluates against (user, instance_context) and returns
(allowed: bool, reason: str). Guards compose with AND semantics.
"""
import operator

OPS = {
    "==": operator.eq, "!=": operator.ne,
    ">": operator.gt, ">=": operator.ge,
    "<": operator.lt, "<=": operator.le,
    "in": lambda a, b: a in b,
}


class GuardError(Exception):
    pass


def permission_guard(user, context, config):
    perm = config.get("permission")
    if not perm:
        raise GuardError("permission guard missing 'permission'")
    ok = user.has_perm(perm)
    return ok, "" if ok else f"missing permission {perm}"


def role_guard(user, context, config):
    roles = set(config.get("roles", []))
    user_roles = set(user.groups.values_list("name", flat=True))
    ok = bool(roles & user_roles)
    return ok, "" if ok else f"requires one of roles {sorted(roles)}"


def condition_guard(user, context, config):
    """Evaluates: context[field] <op> value  (no eval(), whitelisted ops only)."""
    field, op, value = config.get("field"), config.get("op", "=="), config.get("value")
    if op not in OPS:
        raise GuardError(f"unsupported operator {op}")
    actual = context.get(field)
    ok = OPS[op](actual, value)
    return ok, "" if ok else f"condition failed: {field} {op} {value!r} (actual={actual!r})"


def amount_guard(user, context, config):
    """Approval-limit guard: amount in context must be <= user's limit."""
    amount = float(context.get(config.get("field", "amount"), 0))
    limit = float(config.get("max_amount", 0))
    ok = amount <= limit
    return ok, "" if ok else f"amount {amount} exceeds limit {limit}"


GUARDS = {
    "permission": permission_guard,
    "role": role_guard,
    "condition": condition_guard,
    "amount": amount_guard,
}


def evaluate_guards(guards: list[dict], user, context: dict) -> tuple[bool, list[str]]:
    reasons = []
    for g in guards or []:
        fn = GUARDS.get(g.get("type"))
        if fn is None:
            raise GuardError(f"unknown guard type {g.get('type')}")
        ok, reason = fn(user, context, g.get("config", {}))
        if not ok:
            reasons.append(reason)
    return not reasons, reasons
