from __future__ import annotations

from abx.evidence.readinessReports import build_readiness_report
from abx.evidence.sufficiencyReports import build_sufficiency_report
from abx.evidence.thresholdReports import build_threshold_report
from abx.evidence.transitionReports import build_evidence_transition_report
from abx.evidence.types import EvidenceGovernanceScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _category(*, blocked: bool, provisional: bool, conflict: bool, unmet: bool) -> str:
    if blocked:
        return "BLOCKED"
    if conflict:
        return "CONFLICT_BURDENED"
    if provisional:
        return "PROVISIONAL_BURDENED"
    if unmet:
        return "PARTIAL"
    return "SUFFICIENCY_READY"


def build_evidence_governance_scorecard() -> EvidenceGovernanceScorecard:
    threshold = build_threshold_report()
    sufficiency = build_sufficiency_report()
    readiness = build_readiness_report()
    transitions = build_evidence_transition_report()

    suff_states = [x["sufficiency_state"] for x in sufficiency["sufficiency"]]
    ready_states = [x["readiness_state"] for x in readiness["readiness"]]

    conflict = "CONFLICTING_EVIDENCE" in suff_states
    unmet = "BURDEN_UNMET" in suff_states
    provisional = "BURDEN_PROVISIONALLY_MET" in suff_states
    blocked = any(x in {"ESCALATED", "ABSTAINED"} for x in ready_states)

    dimensions = {
        "threshold_state_clarity": "EXPLICIT",
        "burden_of_proof_explicitness": "EXPLICIT",
        "sufficiency_classification_quality": "CONFLICT_PRESENT" if conflict else "DISCIPLINED",
        "abstain_defer_escalate_legibility": "VISIBLE",
        "provisional_decision_hygiene": "ELEVATED" if provisional else "LOW",
        "conflicting_evidence_visibility": "VISIBLE" if transitions["conflicts"] else "PARTIAL",
        "unmet_burden_visibility": "VISIBLE" if transitions["unmetBurden"] else "PARTIAL",
        "stale_provisional_burden": "ELEVATED" if any(x["provisional_state"] == "PROVISIONAL_DECISION_EXPIRED" for x in transitions["provisional"]) else "LOW",
        "decision_readiness_clarity": "BLOCKED" if blocked else "EXPLICIT",
        "operator_evidence_posture_clarity": "EXPLICIT",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"CONFLICT_PRESENT", "ELEVATED", "BLOCKED", "NOT_COMPUTABLE"})
    evidence = {
        "threshold": [threshold["auditHash"]],
        "sufficiency": [sufficiency["auditHash"]],
        "readiness": [readiness["auditHash"]],
        "transitions": [transitions["auditHash"]],
    }
    category = _category(blocked=blocked, provisional=provisional, conflict=conflict, unmet=unmet)
    scorecard_hash = sha256_bytes(dumps_stable({"dimensions": dimensions, "evidence": evidence, "blockers": blockers, "category": category}).encode("utf-8"))
    return EvidenceGovernanceScorecard(
        artifact_type="EvidenceGovernanceScorecard.v1",
        artifact_id="evidence-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        category=category,
        scorecard_hash=scorecard_hash,
    )
