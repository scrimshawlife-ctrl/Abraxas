from __future__ import annotations

from abx.performance.performanceInventory import build_performance_surface_inventory


def classify_performance_surfaces() -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {
        "critical_path": [],
        "important_non_critical": [],
        "background_auxiliary": [],
        "legacy_redundant_candidate": [],
    }
    for record in build_performance_surface_inventory():
        buckets[record.criticality].append(record.surface_id)
    return {k: sorted(v) for k, v in buckets.items()}


def classify_performance_cost_classes() -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {
        "core_runtime": [],
        "observability_overhead": [],
        "adapter_overhead": [],
        "governance_overhead": [],
        "optional_operator": [],
    }
    for record in build_performance_surface_inventory():
        buckets[record.cost_class].append(record.surface_id)
    return {k: sorted(v) for k, v in buckets.items()}


def detect_duplicate_performance_vocabulary() -> list[str]:
    allowed = {
        "critical_path",
        "important_non_critical",
        "background_auxiliary",
        "legacy_redundant_candidate",
    }
    invalid = sorted({x.criticality for x in build_performance_surface_inventory() if x.criticality not in allowed})
    return invalid
