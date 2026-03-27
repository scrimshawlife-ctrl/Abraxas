from __future__ import annotations

from abx.closure.closureInventory import build_closure_surface_inventory
from abx.closure.types import ClosureDependencyRecord


HEALTHY_CLOSURE_STATES = {"CLOSURE_COMPLETE", "CLOSURE_COMPLETE_WITH_WAIVERS"}


def build_closure_dependencies() -> list[ClosureDependencyRecord]:
    rows = [
        ClosureDependencyRecord(
            dependency_id=f"dep.{surface.domain_id}",
            domain_id=surface.domain_id,
            depends_on=sorted(surface.dependency_ids),
        )
        for surface in build_closure_surface_inventory()
    ]
    return sorted(rows, key=lambda x: x.dependency_id)


def classify_dependency_states(domain_states: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in build_closure_dependencies():
        if not row.depends_on:
            out[row.dependency_id] = "DEPENDENCY_SATISFIED"
            continue
        missing = [dep for dep in row.depends_on if dep not in domain_states]
        blocked = [dep for dep in row.depends_on if domain_states.get(dep) not in HEALTHY_CLOSURE_STATES]
        if missing:
            out[row.dependency_id] = "NOT_COMPUTABLE"
        elif blocked:
            out[row.dependency_id] = "DEPENDENCY_BLOCKED"
        else:
            out[row.dependency_id] = "DEPENDENCY_SATISFIED"
    return out
