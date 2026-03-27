from __future__ import annotations

from abx.obligations.commitmentReports import build_external_commitment_report
from abx.obligations.dueStateReports import build_due_state_report
from abx.obligations.obligationReports import build_obligation_lifecycle_report
from abx.obligations.transitionReports import build_obligation_transition_report
from abx.obligations.types import ObligationGovernanceScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _category(*, missed: bool, blocked: bool, risk: bool) -> str:
    if blocked:
        return "BLOCKED"
    if missed:
        return "MISS_BURDENED"
    if risk:
        return "RISK_LADEN"
    return "COMMITMENT_READY"


def build_obligation_governance_scorecard() -> ObligationGovernanceScorecard:
    commitment = build_external_commitment_report()
    due = build_due_state_report()
    lifecycle = build_obligation_lifecycle_report()
    transitions = build_obligation_transition_report()

    missed = any(v == "MISSED" for v in lifecycle["obligationStates"].values())
    blocked = any(v == "BLOCKED" for v in lifecycle["obligationStates"].values())
    risk = any(x["risk_state"] == "AT_RISK" for x in due["dueStates"])

    dimensions = {
        "commitment_state_clarity": "EXPLICIT",
        "due_state_quality": "RISK_LADEN" if risk else "DISCIPLINED",
        "discharge_evidence_quality": "PARTIAL" if any(v == "PARTIALLY_DISCHARGED" for v in lifecycle["obligationStates"].values()) else "COMPLETE",
        "risk_slip_miss_visibility": "VISIBLE",
        "supersession_cancellation_explicitness": "EXPLICIT" if transitions["superseded"] or transitions["canceled"] else "PARTIAL",
        "stale_obligation_burden": "ELEVATED" if missed else "LOW",
        "partial_fulfillment_visibility": "VISIBLE",
        "trust_surface_legibility": "EXPLICIT",
        "reevaluation_discipline": "ENFORCED",
        "operator_obligation_clarity": "EXPLICIT",
    }
    blockers = sorted(
        k for k, v in dimensions.items() if v in {"RISK_LADEN", "ELEVATED", "BLOCKED", "NOT_COMPUTABLE"}
    )
    evidence = {
        "commitment": [commitment["auditHash"]],
        "due": [due["auditHash"]],
        "lifecycle": [lifecycle["auditHash"]],
        "transitions": [transitions["auditHash"]],
        "missed": sorted(k for k, v in lifecycle["obligationStates"].items() if v == "MISSED"),
    }
    category = _category(missed=missed, blocked=blocked, risk=risk)
    digest = sha256_bytes(dumps_stable({"dimensions": dimensions, "evidence": evidence, "blockers": blockers, "category": category}).encode("utf-8"))
    return ObligationGovernanceScorecard(
        artifact_type="ObligationGovernanceScorecard.v1",
        artifact_id="obligation-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        category=category,
        scorecard_hash=digest,
    )
