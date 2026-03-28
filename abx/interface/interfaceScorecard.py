from __future__ import annotations

from abx.interface.acceptanceReports import build_receiver_acceptance_report
from abx.interface.contractReports import build_interface_contract_report
from abx.interface.handoffReports import build_handoff_reliability_report
from abx.interface.transitionReports import build_interface_transition_report
from abx.interface.types import CrossBoundaryDeliveryScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _category(*, blocked: bool, degraded: bool, mismatch: bool, partial: bool, not_computable: bool) -> str:
    if not_computable:
        return "NOT_COMPUTABLE"
    if blocked:
        return "BLOCKED"
    if mismatch:
        return "MISMATCH_BURDENED"
    if degraded:
        return "DEGRADED_HANDOFF_BURDENED"
    if partial:
        return "PARTIAL"
    return "CROSS_BOUNDARY_GOVERNED"


def build_cross_boundary_delivery_scorecard() -> CrossBoundaryDeliveryScorecard:
    contracts = build_interface_contract_report()
    handoff = build_handoff_reliability_report()
    acceptance = build_receiver_acceptance_report()
    transitions = build_interface_transition_report()

    not_computable = any(v == "NOT_COMPUTABLE" for v in contracts["contractStates"].values()) or any(
        v == "NOT_COMPUTABLE" for v in handoff["handoffStates"].values()
    ) or any(v == "NOT_COMPUTABLE" for v in acceptance["acceptanceStates"].values())
    blocked = any(v == "CONTRACT_BROKEN" for v in contracts["contractStates"].values()) or any(
        v in {"HANDOFF_FAILED"} for v in handoff["handoffStates"].values()
    ) or any(v in {"REJECTED", "COERCED_DEFAULTED", "INTERPRETATION_MISMATCH"} for v in acceptance["acceptanceStates"].values())
    mismatch = any(x["mismatch_state"] in {"MISMATCHED_DELIVERY", "REJECTED_DELIVERY"} for x in transitions["mismatch"]) 
    degraded = any(x["degraded_state"] in {"DELIVERY_STALE", "DELIVERY_DUPLICATED", "TRUST_DOWNGRADED"} for x in transitions["degraded"]) 
    partial = any(x["degraded_state"] in {"DELIVERY_PARTIAL", "REDELIVERY_REQUIRED"} for x in transitions["degraded"]) 

    dimensions = {
        "contract_clarity": "DEGRADED"
        if any(v in {"CONTRACT_DRIFT_SUSPECTED", "NOT_COMPUTABLE"} for v in contracts["contractStates"].values())
        else "CLEAR",
        "delivery_integrity": "AT_RISK" if degraded or partial else "DISCIPLINED",
        "acceptance_legitimacy": "AT_RISK"
        if any(v in {"REJECTED", "COERCED_DEFAULTED", "INTERPRETATION_MISMATCH", "NOT_COMPUTABLE"} for v in acceptance["acceptanceStates"].values())
        else "DISCIPLINED",
        "interpretation_correctness": "AT_RISK"
        if any(x["interpretation_state"] in {"INTERPRETATION_COERCED", "INTERPRETATION_MISMATCH", "NOT_COMPUTABLE"} for x in acceptance["interpretation"])
        else "DISCIPLINED",
        "degraded_handoff_burden": "ELEVATED" if degraded or partial or mismatch else "LOW",
        "operator_boundary_clarity": "EXPLICIT",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"DEGRADED", "AT_RISK", "ELEVATED"})
    blockers.extend(sorted(x["code"] for x in contracts["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in handoff["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in acceptance["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in transitions["governanceErrors"] if x["severity"] == "ERROR"))
    blockers = sorted(set(blockers))

    evidence = {
        "contracts": [contracts["auditHash"]],
        "handoff": [handoff["auditHash"]],
        "acceptance": [acceptance["auditHash"]],
        "transitions": [transitions["auditHash"]],
    }
    category = _category(blocked=blocked, degraded=degraded, mismatch=mismatch, partial=partial, not_computable=not_computable)
    payload = {"dimensions": dimensions, "evidence": evidence, "blockers": blockers, "category": category}
    return CrossBoundaryDeliveryScorecard(
        artifact_type="CrossBoundaryDeliveryScorecard.v1",
        artifact_id="cross-boundary-delivery-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        category=category,
        scorecard_hash=sha256_bytes(dumps_stable(payload).encode("utf-8")),
    )
