from __future__ import annotations

from abx.agency.actionBoundaryReports import build_action_boundary_report
from abx.agency.autonomousReports import build_autonomous_operation_report
from abx.agency.delegationReports import build_delegation_report
from abx.agency.guardrailReports import build_guardrail_report
from abx.agency.types import AutonomousOperationScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _category(*, posture: str, delegation: str, guardrail: str, hidden_suspected: bool) -> str:
    if hidden_suspected:
        return "HIDDEN_CHANNEL_RISK"
    if posture in {"BLOCKED", "NOT_COMPUTABLE"}:
        return "BLOCKED"
    if guardrail in {"BLOCKED", "DEGRADED"}:
        return "PARTIAL"
    if posture == "ANALYSIS_ONLY":
        return "ANALYSIS_ONLY"
    if posture in {"OPERATOR_CONFIRMED_ACTION", "DELEGATED_ACTION", "BOUNDED_AUTONOMOUS_ACTION"} and delegation == "DELEGATION_READY":
        return "BOUNDED_ACTION_READY"
    return "PARTIAL"


def build_agency_governance_scorecard() -> AutonomousOperationScorecard:
    autonomous = build_autonomous_operation_report()
    delegation = build_delegation_report()
    guardrail = build_guardrail_report()
    boundary = build_action_boundary_report()

    hidden_suspected = bool(boundary["classification"]["hidden_channel_suspected"])
    dimensions = {
        "action_mode_clarity": "EXPLICIT",
        "authority_scope_boundedness": "BOUNDED" if autonomous["autonomousPosture"] != "NOT_COMPUTABLE" else "NOT_COMPUTABLE",
        "delegation_chain_integrity": delegation["delegationPosture"],
        "recursion_fanout_containment": "CONTAINED" if not delegation["blockedChains"] else "BLOCKED",
        "guardrail_coverage_quality": guardrail["guardrailPosture"],
        "guardrail_trip_visibility": "VISIBLE" if guardrail["trippedPolicies"] else "CLEAR",
        "hidden_channel_burden": "SUSPECTED" if hidden_suspected else "CLEAR",
        "action_boundary_clarity": "EXPLICIT",
        "confirmation_gate_clarity": "EXPLICIT",
        "safe_stop_readiness": "READY" if guardrail["guardrailPosture"] in {"GUARDRAILED", "DEGRADED"} else "PARTIAL",
        "operator_agency_state_clarity": "EXPLICIT",
    }
    blockers = sorted(
        k
        for k, v in dimensions.items()
        if v in {"BLOCKED", "NOT_COMPUTABLE", "SUSPECTED"}
    )
    category = _category(
        posture=autonomous["autonomousPosture"],
        delegation=delegation["delegationPosture"],
        guardrail=guardrail["guardrailPosture"],
        hidden_suspected=hidden_suspected,
    )
    evidence = {
        "autonomous": [autonomous["auditHash"]],
        "delegation": [delegation["auditHash"]],
        "guardrail": [guardrail["auditHash"]],
        "boundary": [boundary["auditHash"]],
        "trippedPolicies": guardrail["trippedPolicies"],
        "hiddenChannels": boundary["classification"]["hidden_channel_suspected"],
    }
    digest = sha256_bytes(dumps_stable({"dimensions": dimensions, "evidence": evidence, "blockers": blockers, "category": category}).encode("utf-8"))
    return AutonomousOperationScorecard(
        artifact_type="AgencyGovernanceScorecard.v1",
        artifact_id="agency-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        category=category,
        scorecard_hash=digest,
    )
