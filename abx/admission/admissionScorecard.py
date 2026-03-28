from __future__ import annotations

from abx.admission.admissionReports import build_change_admission_report
from abx.admission.promotionReports import build_promotion_gate_report
from abx.admission.releaseReports import build_release_readiness_report
from abx.admission.rollbackReports import build_rejection_rollback_report
from abx.admission.types import AdmissionGovernanceScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _category(*, blocked: bool, rollback: bool, provisional: bool, partial: bool, not_computable: bool) -> str:
    if not_computable:
        return "NOT_COMPUTABLE"
    if blocked:
        return "BLOCKED"
    if rollback:
        return "ROLLBACK_BURDENED"
    if provisional:
        return "PROVISIONAL_BURDENED"
    if partial:
        return "PARTIAL"
    return "ADMISSION_GOVERNED"


def build_admission_governance_scorecard() -> AdmissionGovernanceScorecard:
    admission = build_change_admission_report()
    promotion = build_promotion_gate_report()
    release = build_release_readiness_report()
    rollback = build_rejection_rollback_report()

    not_computable = any(v == "NOT_COMPUTABLE" for v in admission["admissionStates"].values()) or any(
        v == "NOT_COMPUTABLE" for v in promotion["promotionStates"].values()
    ) or any(v == "NOT_COMPUTABLE" for v in release["readinessStates"].values())
    blocked = any(v in {"ADMISSION_REJECTED", "ADMISSION_BLOCKED"} for v in admission["admissionStates"].values()) or any(
        v == "PROMOTION_FAILED_GATE" for v in promotion["promotionStates"].values()
    ) or any(v == "RELEASE_BLOCKED" for v in release["readinessStates"].values())
    rollback_active = any(x["rollback_state"] == "ROLLBACK_TRIGGERED" for x in rollback["rollback"])
    provisional = any(v in {"RELEASE_PROVISIONAL", "EXPERIMENTAL"} for v in release["readinessStates"].values()) or any(
        v in {"PROMOTION_GATED", "PROMOTION_DEFERRED", "PROMOTION_CANDIDATE"} for v in promotion["promotionStates"].values()
    )
    partial = any(v in {"CHANGE_PROPOSED", "ADMISSION_PENDING"} for v in admission["admissionStates"].values())

    dimensions = {
        "admission_clarity": "DEGRADED"
        if any(v in {"CHANGE_PROPOSED", "ADMISSION_PENDING", "NOT_COMPUTABLE"} for v in admission["admissionStates"].values())
        else "CLEAR",
        "promotion_legitimacy": "AT_RISK"
        if any(v in {"PROMOTION_FAILED_GATE", "PROMOTION_DEFERRED", "NOT_COMPUTABLE"} for v in promotion["promotionStates"].values())
        else "DISCIPLINED",
        "readiness_validity": "AT_RISK"
        if any(v in {"EXPERIMENTAL", "RELEASE_PROVISIONAL", "RELEASE_BLOCKED", "NOT_COMPUTABLE"} for v in release["readinessStates"].values())
        else "DISCIPLINED",
        "rollback_discipline": "ENFORCED" if rollback_active else "PARTIAL",
        "unresolved_risk_visibility": "ELEVATED" if blocked or provisional or rollback_active else "LOW",
        "operator_release_clarity": "EXPLICIT",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"DEGRADED", "AT_RISK", "ELEVATED"})
    blockers.extend(sorted(x["code"] for x in admission["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in promotion["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in release["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in rollback["governanceErrors"] if x["severity"] == "ERROR"))
    blockers = sorted(set(blockers))

    evidence = {
        "admission": [admission["auditHash"]],
        "promotion": [promotion["auditHash"]],
        "release": [release["auditHash"]],
        "rollback": [rollback["auditHash"]],
    }
    category = _category(
        blocked=blocked,
        rollback=rollback_active,
        provisional=provisional,
        partial=partial,
        not_computable=not_computable,
    )
    payload = {"dimensions": dimensions, "evidence": evidence, "blockers": blockers, "category": category}
    return AdmissionGovernanceScorecard(
        artifact_type="AdmissionGovernanceScorecard.v1",
        artifact_id="admission-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        category=category,
        scorecard_hash=sha256_bytes(dumps_stable(payload).encode("utf-8")),
    )
