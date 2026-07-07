"""Decision Engine: declarative business rules with explainable outcomes.

Rules are (condition, action, priority) triples evaluated against a
context dict. Unlike guards (which gate a single transition), this engine
resolves *what to do* — e.g. auto-approve, route for review, flag — and
returns the winning rule plus the full trace for auditability.
"""
import operator

OPS = {'==': operator.eq, '!=': operator.ne, '>': operator.gt,
       '>=': operator.ge, '<': operator.lt, '<=': operator.le,
       'in': lambda a, b: a in b, 'contains': lambda a, b: b in (a or '')}


class Rule:
    def __init__(self, name, conditions, outcome, priority=0):
        # conditions: list of (field, op, value) — AND semantics
        self.name = name
        self.conditions = conditions
        self.outcome = outcome
        self.priority = priority

    def matches(self, ctx) -> tuple[bool, list]:
        trace = []
        for field, op, value in self.conditions:
            actual = ctx.get(field)
            ok = OPS[op](actual, value) if op in OPS else False
            trace.append({'field': field, 'op': op, 'expected': value,
                          'actual': actual, 'ok': ok})
            if not ok:
                return False, trace
        return True, trace


class DecisionEngine:
    def __init__(self):
        self.rulesets: dict[str, list[Rule]] = {}

    def define(self, domain: str, rules: list[Rule]):
        self.rulesets[domain] = sorted(rules, key=lambda r: -r.priority)

    def decide(self, domain: str, context: dict) -> dict:
        traces = []
        for rule in self.rulesets.get(domain, []):
            ok, trace = rule.matches(context)
            traces.append({'rule': rule.name, 'matched': ok, 'trace': trace})
            if ok:
                return {'decision': rule.outcome, 'rule': rule.name,
                        'explanation': traces}
        return {'decision': 'no_match', 'rule': None, 'explanation': traces}


engine = DecisionEngine()

# default: purchase-order approval routing
engine.define('po_approval', [
    Rule('auto_approve_small',
         [('amount', '<', 5000)], {'action': 'auto_approve'}, priority=10),
    Rule('manager_review',
         [('amount', '<', 50000)], {'action': 'route', 'to': 'manager'},
         priority=5),
    Rule('cfo_review',
         [('amount', '>=', 50000)], {'action': 'route', 'to': 'cfo'},
         priority=1),
])
