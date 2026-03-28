from __future__ import annotations

from abx.observability.blindSpotReports import build_blind_spot_report
from abx.observability.coverageReports import build_observability_coverage_report
from abx.observability.sufficiencyReports import build_measurement_sufficiency_report
from abx.observability.transitionReports import build_observability_transition_report
from abx.observability.types import ObservabilityGovernanceScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _category(*, blocked: bool, blind_spot: bool, insufficient: bool, stale: bool, not_computable: bool, partial: bool) -> str:
    if not_computable:
        return "NOT_COMPUTABLE"
    if blocked:
        return "BLOCKED"
    if blind_spot:
        return "BLIND_SPOT_BURDENED"
    if insufficient:
        return "INSUFFICIENT_MEASUREMENT_BURDENED"
    if stale:
        return "STALE_INSTRUMENTATION_BURDENED"
    if partial:
        return "PARTIAL"
    return "OBSERVABILITY_GOVERNED"


def build_observability_governance_scorecard() -> ObservabilityGovernanceScorecard:
    coverage = build_observability_coverage_report()
    blind = build_blind_spot_report()
    sufficiency = build_measurement_sufficiency_report()
    transitions = build_observability_transition_report()

    not_computable = any(v == "NOT_COMPUTABLE" for v in coverage["coverageStates"].values()) or any(
        v == "NOT_COMPUTABLE" for v in blind["blindSpotStates"].values()
    ) or any(v == "NOT_COMPUTABLE" for v in sufficiency["sufficiencyStates"].values())
    blocked = any(v in {"NO_MEANINGFUL_COVERAGE"} for v in coverage["coverageStates"].values()) or any(
        v in {"BLIND_SPOT_BLOCKED", "BLIND_SPOT_HIGH_RISK"} for v in blind["blindSpotStates"].values()
    ) or any(v in {"HIGH_CONSEQUENCE_UNDER_OBSERVED"} for v in sufficiency["sufficiencyStates"].values())
    blind_spot = any(v in {"BLIND_SPOT_SUSPECTED", "BLIND_SPOT_CONFIRMED"} for v in blind["blindSpotStates"].values())
    insufficient = any(v in {"INSUFFICIENT_MEASUREMENT", "MEASUREMENT_AMBIGUOUS", "HIGH_CONSEQUENCE_UNDER_OBSERVED"} for v in sufficiency["sufficiencyStates"].values())
    stale = any(x["freshness_state"] in {"INSTRUMENTATION_STALE", "REFRESH_INSTRUMENTATION_REQUIRED"} for x in transitions["freshness"])
    partial = any(v in {"COVERAGE_PARTIAL", "COVERAGE_DEGRADED", "COVERAGE_UNKNOWN"} for v in coverage["coverageStates"].values())

    dimensions = {
        "coverage_clarity": "DEGRADED" if partial or not_computable else "CLEAR",
        "blind_spot_visibility": "ELEVATED" if blind_spot else "LOW",
        "sufficiency_legitimacy": "AT_RISK" if insufficient else "DISCIPLINED",
        "stale_instrumentation_burden": "ELEVATED" if stale else "LOW",
        "false_assurance_burden": "ELEVATED"
        if any(x["assurance_state"] in {"FALSE_ASSURANCE_RISK", "CONFIDENCE_BLOCKED"} for x in transitions["assurance"])
        else "LOW",
        "operator_observability_clarity": "EXPLICIT",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"DEGRADED", "AT_RISK", "ELEVATED"})
    blockers.extend(sorted(x["code"] for x in coverage["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in blind["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in sufficiency["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in transitions["governanceErrors"] if x["severity"] == "ERROR"))
    blockers = sorted(set(blockers))

    evidence = {
        "coverage": [coverage["auditHash"]],
        "blind": [blind["auditHash"]],
        "sufficiency": [sufficiency["auditHash"]],
        "transitions": [transitions["auditHash"]],
    }
    category = _category(
        blocked=blocked,
        blind_spot=blind_spot,
        insufficient=insufficient,
        stale=stale,
        not_computable=not_computable,
        partial=partial,
    )
    payload = {"dimensions": dimensions, "evidence": evidence, "blockers": blockers, "category": category}
    return ObservabilityGovernanceScorecard(
        artifact_type="ObservabilityGovernanceScorecard.v1",
        artifact_id="observability-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        category=category,
        scorecard_hash=sha256_bytes(dumps_stable(payload).encode("utf-8")),
    )
