from __future__ import annotations

from abx.operator.interventionReports import build_intervention_report
from abx.operator.operatorTransitions import build_operator_transition_records
from abx.operator.overrideReports import build_override_report
from abx.operator.traceReports import build_traceability_report
from abx.operator.transitionReports import build_operator_transition_report
from abx.operator.types import OperatorGovernanceScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _category(*, blockers: list[str], trust_downgraded: bool, restoration_gap: bool) -> str:
    if blockers:
        return "BLOCKED"
    if trust_downgraded or restoration_gap:
        return "TRUST_DOWNGRADED"
    return "GOVERNED"


def build_operator_governance_scorecard() -> OperatorGovernanceScorecard:
    overrides = build_override_report()
    interventions = build_intervention_report()
    traces = build_traceability_report()
    transitions = build_operator_transition_report()

    override_states = set(overrides["overrideStates"].values())
    intervention_states = set(interventions["interventionLegitimacy"].values())
    trace_states = set(traces["traceCompleteness"].values())
    reason_states = set(traces["reasonQuality"].values())
    scope_states = {x["scope_state"] for x in traces["scopeRecords"]}
    restoration_required = any(x["restoration_required"] == "YES" for x in traces["reversibilityRecords"])
    trust_downgraded = any(x["drift_state"] == "TRUST_DOWNGRADED" for x in transitions["manualDrift"])
    overbroad_active = "OVERRIDE_OVERBROAD_ACTIVE" in set(transitions["transitionStates"].values())

    dimensions = {
        "override_legitimacy": "WEAK" if "OVERRIDE_FORBIDDEN" in override_states else "EXPLICIT",
        "intervention_boundedness": "OVERBROAD" if overbroad_active else "BOUNDED",
        "traceability_quality": "PARTIAL" if "TRACE_PARTIAL" in trace_states else "COMPLETE",
        "reason_quality": "INSUFFICIENT_PRESENT" if "REASON_INSUFFICIENT" in reason_states else "EXPLICIT",
        "scope_boundedness": "OVERBROAD_PRESENT" if "SCOPE_OVERBROAD" in scope_states else "BOUNDED",
        "restoration_hygiene": "RESTORATION_REQUIRED" if restoration_required else "RESTORED",
        "manual_drift_burden": "ELEVATED" if transitions["manualDrift"] else "LOW",
        "legitimacy_discipline": "ILLEGITIMATE_PRESENT" if "MANUAL_INTERVENTION_ILLEGITIMATE" in intervention_states else "HEALTHY",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"WEAK", "OVERBROAD", "OVERBROAD_PRESENT", "ILLEGITIMATE_PRESENT"})
    category = _category(
        blockers=blockers,
        trust_downgraded=trust_downgraded,
        restoration_gap=restoration_required,
    )
    evidence = {
        "override": [overrides["auditHash"]],
        "intervention": [interventions["auditHash"]],
        "traceability": [traces["auditHash"]],
        "transition": [transitions["auditHash"]],
    }
    scorecard_hash = sha256_bytes(dumps_stable({"dimensions": dimensions, "evidence": evidence, "blockers": blockers, "category": category}).encode("utf-8"))
    return OperatorGovernanceScorecard(
        artifact_type="OperatorGovernanceScorecard.v1",
        artifact_id="operator-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        category=category,
        scorecard_hash=scorecard_hash,
    )
