from __future__ import annotations

from abx.freshness.freshnessReports import build_freshness_decay_report
from abx.freshness.horizonReports import build_time_horizon_report
from abx.freshness.stalenessReports import build_staleness_report
from abx.freshness.transitionReports import build_freshness_transition_report
from abx.freshness.types import FreshnessGovernanceScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _category(*, blocked: bool, age_risk: bool, refresh_overdue: bool, not_computable: bool, partial: bool) -> str:
    if not_computable:
        return "NOT_COMPUTABLE"
    if blocked:
        return "BLOCKED"
    if refresh_overdue:
        return "REFRESH_OVERDUE_BURDENED"
    if age_risk:
        return "AGE_RISK_BURDENED"
    if partial:
        return "PARTIAL"
    return "FRESHNESS_GOVERNED"


def build_freshness_governance_scorecard() -> FreshnessGovernanceScorecard:
    horizon = build_time_horizon_report()
    freshness = build_freshness_decay_report()
    staleness = build_staleness_report()
    transitions = build_freshness_transition_report()

    not_computable = any(v in {"HORIZON_UNKNOWN", "NOT_COMPUTABLE"} for v in horizon["horizonStates"].values()) or any(
        v == "DECAY_UNKNOWN" for v in freshness["freshnessStates"].values()
    )
    blocked = any(v == "REUSE_BLOCKED" for v in freshness["freshnessStates"].values())
    refresh_overdue = any(x["to_state"] == "REFRESH_OVERDUE" for x in transitions["transitions"])
    age_risk = any(v in {"STALE", "EXPIRED", "ARCHIVAL_ONLY", "REFRESH_REQUIRED"} for v in freshness["freshnessStates"].values()) or any(
        x["staleness_state"] in {"STALE_SUPPORT_ACTIVE", "EXPIRED_FOR_OPERATIONAL_USE"} for x in staleness["staleness"]
    )
    partial = any(v in {"FRESH_WITH_WARNING", "AGING"} for v in freshness["freshnessStates"].values())

    dimensions = {
        "horizon_clarity": "DEGRADED" if not_computable else "CLEAR",
        "freshness_classification_quality": "AT_RISK" if age_risk else "DISCIPLINED",
        "decay_model_appropriateness": "AT_RISK"
        if any(x["decay_state"] == "DECAY_UNKNOWN" for x in freshness["decay"])
        else "DISCIPLINED",
        "stale_support_visibility": "VISIBLE"
        if any(x["support_state"] == "STALE_SUPPORT_ACTIVE" for x in transitions["staleSupport"])
        else "LOW",
        "expiry_archival_distinction_quality": "AT_RISK"
        if any(x["expiry_state"] in {"EXPIRED", "ARCHIVAL_ONLY"} for x in transitions["expiry"])
        else "CLEAR",
        "refresh_discipline": "REQUIRED"
        if any(x["to_state"] in {"REFRESH_REQUIRED", "REFRESH_OVERDUE"} for x in transitions["transitions"])
        else "STABLE",
        "age_risk_visibility": "ELEVATED" if age_risk else "LOW",
        "reuse_block_legitimacy": "ENFORCED" if blocked else "PARTIAL",
        "trust_downgrade_discipline": "ENFORCED" if age_risk else "PARTIAL",
        "operator_freshness_posture_clarity": "EXPLICIT",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"DEGRADED", "AT_RISK", "REQUIRED", "ELEVATED"})
    blockers.extend(sorted(x["code"] for x in horizon["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in freshness["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in staleness["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in transitions["governanceErrors"] if x["severity"] == "ERROR"))
    blockers = sorted(set(blockers))

    evidence = {
        "horizon": [horizon["auditHash"]],
        "freshness": [freshness["auditHash"]],
        "staleness": [staleness["auditHash"]],
        "transitions": [transitions["auditHash"]],
    }
    category = _category(
        blocked=blocked,
        age_risk=age_risk,
        refresh_overdue=refresh_overdue,
        not_computable=not_computable,
        partial=partial,
    )
    payload = {"dimensions": dimensions, "evidence": evidence, "blockers": blockers, "category": category}
    return FreshnessGovernanceScorecard(
        artifact_type="FreshnessGovernanceScorecard.v1",
        artifact_id="freshness-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        category=category,
        scorecard_hash=sha256_bytes(dumps_stable(payload).encode("utf-8")),
    )
