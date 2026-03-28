from __future__ import annotations

from abx.tradeoff.types import ObjectiveConflictRecord, SacrificeRecord, TradeoffRecord


def build_tradeoff_inventory() -> tuple[TradeoffRecord, ...]:
    return (
        TradeoffRecord("trd.release", "release.deploy", "TRADEOFF_LEGIBLE", "safety", "speed"),
        TradeoffRecord("trd.queue", "scheduler.dispatch", "WEIGHTED_TRADEOFF_ACTIVE", "latency", "cost"),
        TradeoffRecord("trd.incident", "incident.response", "DOMINATION_SELECTED", "containment", "throughput"),
        TradeoffRecord("trd.card", "dashboard.summary", "TRADEOFF_HIDDEN", "brevity", "nuance"),
        TradeoffRecord("trd.ops", "operator.routing", "TRADEOFF_LEGIBLE", "coherence", "latency"),
    )


def build_sacrifice_inventory() -> tuple[SacrificeRecord, ...]:
    return (
        SacrificeRecord("sac.release", "release.deploy", "SACRIFICE_ACKNOWLEDGED", "speed_budget"),
        SacrificeRecord("sac.queue", "scheduler.dispatch", "SACRIFICE_ACKNOWLEDGED", "cost_buffer"),
        SacrificeRecord("sac.incident", "incident.response", "SACRIFICE_ACKNOWLEDGED", "throughput_window"),
        SacrificeRecord("sac.card", "dashboard.summary", "HIDDEN_SACRIFICE_RISK", "uncertainty_context"),
        SacrificeRecord("sac.ops", "operator.routing", "SACRIFICE_CLEAR", "minimal"),
    )


def build_objective_conflict_inventory() -> tuple[ObjectiveConflictRecord, ...]:
    return (
        ObjectiveConflictRecord("cnf.release", "release.deploy", "OBJECTIVE_CONFLICT_ACTIVE", "OBJECTIVE_CONFLICT_RESOLVED"),
        ObjectiveConflictRecord("cnf.queue", "scheduler.dispatch", "OBJECTIVE_CONFLICT_ACTIVE", "COMPROMISE_SELECTED"),
        ObjectiveConflictRecord("cnf.incident", "incident.response", "OBJECTIVE_CONFLICT_ACTIVE", "DOMINATION_SELECTED"),
        ObjectiveConflictRecord("cnf.card", "dashboard.summary", "OBJECTIVE_CONFLICT_ACTIVE", "OBJECTIVE_CONFLICT_RESOLVED"),
        ObjectiveConflictRecord("cnf.ops", "operator.routing", "OBJECTIVE_CONFLICT_ACTIVE", "OBJECTIVE_CONFLICT_RESOLVED"),
        ObjectiveConflictRecord("cnf.legacy", "legacy.dispatch", "OBJECTIVE_CONFLICT_ACTIVE", "NOT_COMPUTABLE"),
    )
