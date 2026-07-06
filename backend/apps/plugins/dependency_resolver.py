"""Plugin dependency resolver.

Topological sort with version-range checks (semver-lite: >=, >, <=, <, ==, ~).
Detects cycles, missing dependencies, and version conflicts before install.
"""
import re


class DependencyError(Exception):
    pass


def _parse_version(v: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3] or [0])


def _satisfies(installed: str, spec: str) -> bool:
    if not spec or spec == "*":
        return True
    m = re.match(r"^(>=|<=|==|~|>|<)?\s*([\d.]+)$", spec.strip())
    if not m:
        raise DependencyError(f"bad version spec {spec!r}")
    op, ver = m.group(1) or "==", _parse_version(m.group(2))
    cur = _parse_version(installed)
    if op == "~":  # same major, >= given
        return cur[0] == ver[0] and cur >= ver
    return {"==": cur == ver, ">=": cur >= ver, "<=": cur <= ver,
            ">": cur > ver, "<": cur < ver}[op]


def resolve_install_order(plugins: dict[str, dict]) -> list[str]:
    """plugins: {name: {"version": "1.2.0", "requires": {"other": ">=1.0"}}}
    Returns install order; raises on cycle / missing / conflict."""
    for name, meta in plugins.items():
        for dep, spec in meta.get("requires", {}).items():
            if dep not in plugins:
                raise DependencyError(f"{name} requires missing plugin {dep}")
            if not _satisfies(plugins[dep]["version"], spec):
                raise DependencyError(
                    f"{name} requires {dep} {spec}, "
                    f"but {dep} is {plugins[dep]['version']}"
                )

    order, visiting, done = [], set(), set()

    def visit(node, chain):
        if node in done:
            return
        if node in visiting:
            raise DependencyError(f"dependency cycle: {' -> '.join(chain + [node])}")
        visiting.add(node)
        for dep in plugins[node].get("requires", {}):
            visit(dep, chain + [node])
        visiting.discard(node)
        done.add(node)
        order.append(node)

    for name in sorted(plugins):
        visit(name, [])
    return order
