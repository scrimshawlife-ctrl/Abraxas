from __future__ import annotations

from abx.capacity.commitmentReports import build_capacity_commitment_report
from abx.capacity.contentionReports import build_contention_budget_report
from abx.capacity.reservationReports import build_resource_reservation_report
from abx.capacity.transitionReports import build_capacity_transition_report
from abx.capacity.types import CapacityGovernanceScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _category(*, blocked: bool, exhaustion: bool, overcommitted: bool, starvation: bool, not_computable: bool, partial: bool) -> str:
    if not_computable:
        return "NOT_COMPUTABLE"
    if blocked:
        return "BLOCKED"
    if exhaustion:
        return "EXHAUSTION_BURDENED"
    if overcommitted:
        return "OVERCOMMITTED_BURDENED"
    if starvation:
        return "STARVATION_BURDENED"
    if partial:
        return "PARTIAL"
    return "CAPACITY_GOVERNED"


def build_capacity_governance_scorecard() -> CapacityGovernanceScorecard:
    reservation = build_resource_reservation_report()
    commitment = build_capacity_commitment_report()
    contention = build_contention_budget_report()
    transitions = build_capacity_transition_report()

    not_computable = any(v == "NOT_COMPUTABLE" for v in reservation["reservationStates"].values()) or any(
        v == "NOT_COMPUTABLE" for v in commitment["commitmentStates"].values()
    ) or any(v == "NOT_COMPUTABLE" for v in contention["contentionStates"].values())
    blocked = any(v == "RESERVATION_DENIED" for v in reservation["reservationStates"].values()) or any(
        v == "BLOCKED" for v in commitment["commitmentStates"].values()
    ) or any(v in {"CONTENTION_BLOCKING"} for v in contention["contentionStates"].values())
    exhaustion = any(x["to_state"] == "BUDGET_EXHAUSTED" for x in transitions["transitions"]) or any(
        x["exhaustion_state"] == "BUDGET_EXHAUSTED" for x in transitions["exhaustion"]
    )
    overcommitted = any(v == "OVERCOMMITTED" for v in contention["contentionStates"].values())
    starvation = any(v == "STARVATION_RISK" for v in contention["contentionStates"].values())
    partial = any(v in {"PROVISIONAL_HOLD_ACTIVE", "RESERVATION_EXPIRED"} for v in reservation["reservationStates"].values()) or any(
        v in {"SOFT_CAPACITY_COMMITTED", "BEST_EFFORT_CLAIM", "COMMITMENT_UNKNOWN"} for v in commitment["commitmentStates"].values()
    )

    dimensions = {
        "reservation_clarity": "DEGRADED"
        if any(v in {"PROVISIONAL_HOLD_ACTIVE", "RESERVATION_EXPIRED", "NOT_COMPUTABLE"} for v in reservation["reservationStates"].values())
        else "CLEAR",
        "commitment_legitimacy": "AT_RISK"
        if any(v in {"SOFT_CAPACITY_COMMITTED", "BEST_EFFORT_CLAIM", "COMMITMENT_UNKNOWN", "NOT_COMPUTABLE"} for v in commitment["commitmentStates"].values())
        else "DISCIPLINED",
        "contention_visibility": "ELEVATED" if any(v in {"CONTENTION_ACTIVE", "CONTENTION_BLOCKING"} for v in contention["contentionStates"].values()) else "LOW",
        "exhaustion_posture": "AT_RISK" if exhaustion else "DISCIPLINED",
        "starvation_burden": "ELEVATED" if starvation else "LOW",
        "operator_capacity_clarity": "EXPLICIT",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"DEGRADED", "AT_RISK", "ELEVATED"})
    blockers.extend(sorted(x["code"] for x in reservation["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in commitment["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in contention["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in transitions["governanceErrors"] if x["severity"] == "ERROR"))
    blockers = sorted(set(blockers))

    evidence = {
        "reservation": [reservation["auditHash"]],
        "commitment": [commitment["auditHash"]],
        "contention": [contention["auditHash"]],
        "transitions": [transitions["auditHash"]],
    }
    category = _category(
        blocked=blocked,
        exhaustion=exhaustion,
        overcommitted=overcommitted,
        starvation=starvation,
        not_computable=not_computable,
        partial=partial,
    )
    payload = {"dimensions": dimensions, "evidence": evidence, "blockers": blockers, "category": category}
    return CapacityGovernanceScorecard(
        artifact_type="CapacityGovernanceScorecard.v1",
        artifact_id="capacity-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        category=category,
        scorecard_hash=sha256_bytes(dumps_stable(payload).encode("utf-8")),
    )
