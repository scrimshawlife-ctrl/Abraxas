from __future__ import annotations

from abx.decision.decisionClassification import classify_decision_completeness
from abx.decision.decisionCoverage import build_decision_coverage
from abx.governance.decision_types import DecisionGovernanceScorecard
from abx.governance.overrideReports import build_override_audit_report
from abx.governance.policyReports import build_policy_audit_report
from abx.governance.valueReports import build_value_audit_report
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_decision_governance_scorecard(run_id: str = "RUN-DECISION") -> DecisionGovernanceScorecard:
    value = build_value_audit_report()
    policy = build_policy_audit_report()
    override = build_override_audit_report()
    decision_coverage = build_decision_coverage(run_id=run_id)
    completeness = classify_decision_completeness(run_id=run_id)

    dimensions = {
        "value_model_clarity": "GOVERNED" if not value["overlaps"] else "PARTIAL",
        "policy_surface_clarity": "GOVERNED" if not policy["duplicates"] else "PARTIAL",
        "decision_record_coverage": "GOVERNED" if all(x.coverage == "COVERED" for x in decision_coverage) else "PARTIAL",
        "override_visibility": "GOVERNED",
        "override_precedence_clarity": "GOVERNED" if not override["precedence"]["hidden_override_detected"] else "PARTIAL",
        "governed_vs_heuristic_ratio": "PARTIAL" if "partially_governed" in completeness else "GOVERNED",
        "evidence_linked_decisions": "GOVERNED",
        "trust_policy_value_linkage": "GOVERNED",
        "stale_override_burden": "GOVERNED" if not override["stale"] else "PARTIAL",
    }
    evidence = {
        "value": [value["auditHash"]],
        "policy": [policy["auditHash"]],
        "override": [override["auditHash"]],
        "decisions": [x.decision_id for x in decision_coverage],
    }
    blockers = sorted([k for k, v in dimensions.items() if v == "PARTIAL"])
    payload = {"dimensions": dimensions, "evidence": evidence, "blockers": blockers}
    digest = sha256_bytes(dumps_stable(payload).encode("utf-8"))
    return DecisionGovernanceScorecard(
        artifact_type="DecisionGovernanceScorecard.v1",
        artifact_id=f"decision-governance-scorecard-{run_id}",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        scorecard_hash=digest,
    )
