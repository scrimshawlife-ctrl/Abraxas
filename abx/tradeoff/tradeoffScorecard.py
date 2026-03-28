from __future__ import annotations

from abx.tradeoff.priorityReports import build_priority_assignment_report
from abx.tradeoff.tradeoffReports import build_tradeoff_legibility_report
from abx.tradeoff.transitionReports import build_weighting_transition_report
from abx.tradeoff.types import TradeoffGovernanceScorecard
from abx.tradeoff.weightingReports import build_value_weighting_report
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _category(*, blocked: bool, hidden_weight: bool, override_burden: bool, not_computable: bool, partial: bool) -> str:
    if not_computable:
        return "NOT_COMPUTABLE"
    if blocked:
        return "BLOCKED"
    if hidden_weight:
        return "HIDDEN_WEIGHT_BURDENED"
    if override_burden:
        return "OVERRIDE_BURDENED"
    if partial:
        return "PARTIAL"
    return "TRADEOFF_GOVERNED"


def build_tradeoff_governance_scorecard() -> TradeoffGovernanceScorecard:
    weighting = build_value_weighting_report()
    priority = build_priority_assignment_report()
    tradeoff = build_tradeoff_legibility_report()
    transitions = build_weighting_transition_report()

    not_computable = any(v == "NOT_COMPUTABLE" for v in weighting["weightingStates"].values()) or any(
        v == "PRIORITY_UNKNOWN" for v in priority["priorityStates"].values()
    )
    blocked = any(v == "BLOCKED" for v in priority["priorityStates"].values())
    hidden_weight = any(
        v in {"HIDDEN_WEIGHTING_ACTIVE", "TRADEOFF_HIDDEN"} for v in list(weighting["weightingStates"].values()) + list(tradeoff["tradeoffStates"].values())
    ) or any(x["to_state"] == "HIDDEN_WEIGHTING_ACTIVE" for x in transitions["transitions"])
    override_burden = any(v in {"EMERGENCY_PRIORITY_OVERRIDE", "TEMPORARY_PRIORITY_OVERRIDE"} for v in priority["priorityStates"].values()) or any(
        x["to_state"] == "STICKY_OVERRIDE_DETECTED" for x in transitions["transitions"]
    )
    partial = any(v in {"LOCAL_WEIGHTING_ACTIVE", "SITUATIONAL_PRIORITY", "COMPROMISE_SELECTED"} for v in list(weighting["weightingStates"].values()) + list(priority["priorityStates"].values()) + list(tradeoff["tradeoffStates"].values()))

    dimensions = {
        "weighting_clarity": "DEGRADED" if hidden_weight else "CLEAR",
        "priority_order_legitimacy": "AT_RISK" if override_burden else "DISCIPLINED",
        "override_boundedness": "DEGRADED" if any(x["to_state"] == "STICKY_OVERRIDE_DETECTED" for x in transitions["transitions"]) else "BOUNDED",
        "tradeoff_legibility": "AT_RISK" if any(v == "TRADEOFF_HIDDEN" for v in tradeoff["tradeoffStates"].values()) else "LEGIBLE",
        "sacrifice_acknowledgment_quality": "AT_RISK" if any(x["sacrifice_state"] == "HIDDEN_SACRIFICE_RISK" for x in tradeoff["sacrifice"]) else "ACKNOWLEDGED",
        "hidden_weight_burden": "ELEVATED" if hidden_weight else "LOW",
        "sticky_override_burden": "ELEVATED" if any(x["to_state"] == "STICKY_OVERRIDE_DETECTED" for x in transitions["transitions"]) else "LOW",
        "value_drift_visibility": "VISIBLE" if any(x["drift_state"] == "VALUE_DRIFT_DETECTED" for x in transitions["valueDrift"]) else "LOW",
        "rebalance_discipline": "REQUIRED"
        if any(x["to_state"] in {"LOCAL_OPTIMIZATION_ACTIVE", "VALUE_DRIFT_DETECTED"} for x in transitions["transitions"])
        else "STABLE",
        "operator_prioritization_posture_clarity": "EXPLICIT",
    }

    blockers = sorted(k for k, v in dimensions.items() if v in {"DEGRADED", "AT_RISK", "ELEVATED", "REQUIRED"})
    blockers.extend(sorted(x["code"] for x in weighting["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in priority["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in tradeoff["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in transitions["governanceErrors"] if x["severity"] == "ERROR"))
    blockers = sorted(set(blockers))

    evidence = {
        "weighting": [weighting["auditHash"]],
        "priority": [priority["auditHash"]],
        "tradeoff": [tradeoff["auditHash"]],
        "transitions": [transitions["auditHash"]],
    }
    category = _category(
        blocked=blocked,
        hidden_weight=hidden_weight,
        override_burden=override_burden,
        not_computable=not_computable,
        partial=partial,
    )
    payload = {"dimensions": dimensions, "evidence": evidence, "blockers": blockers, "category": category}
    return TradeoffGovernanceScorecard(
        artifact_type="TradeoffGovernanceScorecard.v1",
        artifact_id="tradeoff-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        category=category,
        scorecard_hash=sha256_bytes(dumps_stable(payload).encode("utf-8")),
    )
