from __future__ import annotations

from abx.tradeoff.types import WeightingTransitionRecord


def build_weighting_transition_records() -> tuple[WeightingTransitionRecord, ...]:
    return (
        WeightingTransitionRecord("wtr.local", "scheduler.dispatch", "CANON_WEIGHTING_ACTIVE", "LOCAL_OPTIMIZATION_ACTIVE", "latency_pressure"),
        WeightingTransitionRecord("wtr.hidden", "legacy.ranker", "CANON_WEIGHTING_ACTIVE", "HIDDEN_WEIGHTING_ACTIVE", "score_bias_untracked"),
        WeightingTransitionRecord("wtr.sticky", "incident.response", "EMERGENCY_PRIORITY_OVERRIDE", "STICKY_OVERRIDE_DETECTED", "incident_closed_override_persisted"),
        WeightingTransitionRecord("wtr.rebalance", "release.deploy", "LOCAL_OPTIMIZATION_ACTIVE", "CANON_PRIORITY_RESTORED", "governance_rebalance"),
        WeightingTransitionRecord("wtr.drift", "dashboard.summary", "TRADEOFF_LEGIBLE", "VALUE_DRIFT_DETECTED", "hidden_sacrifice_accumulation"),
    )
