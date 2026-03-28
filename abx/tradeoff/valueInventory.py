from __future__ import annotations

from abx.tradeoff.types import ValueWeightingRecord


def build_value_inventory() -> tuple[ValueWeightingRecord, ...]:
    return (
        ValueWeightingRecord("wgt.release", "release.deploy", "CANON_WEIGHTING_ACTIVE", "policy/canon-v1", "safety"),
        ValueWeightingRecord("wgt.queue", "scheduler.dispatch", "LOCAL_WEIGHTING_ACTIVE", "runtime/local-tuning", "latency"),
        ValueWeightingRecord("wgt.incident", "incident.response", "EMERGENCY_WEIGHTING_ACTIVE", "incident/override", "containment"),
        ValueWeightingRecord("wgt.recovery", "recovery.path", "TEMPORARY_WEIGHTING_ACTIVE", "ops/temp-window", "uptime"),
        ValueWeightingRecord("wgt.legacy", "legacy.ranker", "NOT_COMPUTABLE", "missing-weight-map", "unknown"),
    )
