"""Runtime boundary: Event Bus, State Machine, Observability.

Infrastructure services consumed by domain apps. Must NOT import from
apps.core.intelligence (dependency direction: intelligence -> runtime,
never the reverse). Import submodules directly, e.g.:
    from apps.core.runtime.event_bus import event_bus
"""
