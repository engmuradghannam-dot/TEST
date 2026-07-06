"""Runtime boundary: Event Bus, State Machine, Observability.

Infrastructure services consumed by domain apps. Must NOT import from
apps.core.intelligence (dependency direction: intelligence -> runtime,
never the reverse).
"""
from . import event_bus, state_machine, observability  # noqa: F401
