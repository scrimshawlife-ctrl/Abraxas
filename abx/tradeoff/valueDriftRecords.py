from __future__ import annotations

from abx.tradeoff.types import ValueDriftRecord


def build_value_drift_records() -> tuple[ValueDriftRecord, ...]:
    return (
        ValueDriftRecord("vdr.queue", "scheduler.dispatch", "LOCAL_OPTIMIZATION_ACTIVE", "speed_wins_7d"),
        ValueDriftRecord("vdr.legacy", "legacy.ranker", "HIDDEN_WEIGHTING_ACTIVE", "weight_source_missing"),
        ValueDriftRecord("vdr.card", "dashboard.summary", "VALUE_DRIFT_DETECTED", "nuance_drop_rate"),
    )
