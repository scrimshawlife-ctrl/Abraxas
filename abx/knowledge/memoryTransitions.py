from __future__ import annotations

from abx.knowledge.memoryLifecycle import build_memory_lifecycle


_ALLOWED = {
    "ACTIVE": {"GOVERNED_DERIVED", "HISTORICAL"},
    "GOVERNED_DERIVED": {"HISTORICAL", "ARCHIVAL"},
    "HISTORICAL": {"ARCHIVAL", "RETIRED"},
    "ARCHIVAL": {"RETIRED"},
    "STALE": {"EXPIRED", "RETIRED"},
}


def validate_memory_transitions() -> dict[str, object]:
    violations: list[str] = []
    for row in build_memory_lifecycle():
        if row.lifecycle_state not in _ALLOWED and row.lifecycle_state not in {"EXPIRED", "RETIRED", "NOT_COMPUTABLE"}:
            violations.append(f"unknown-state:{row.memory_id}:{row.lifecycle_state}")
    return {
        "states": sorted({x.lifecycle_state for x in build_memory_lifecycle()}),
        "violations": sorted(violations),
    }
