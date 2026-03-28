from __future__ import annotations

from abx.reconcile.conflictReports import build_state_conflict_report
from abx.reconcile.reconciliationReports import build_reconciliation_report
from abx.reconcile.restorationReports import build_restoration_status_report
from abx.reconcile.transitionReports import build_reconciliation_transition_report
from abx.reconcile.types import ReconciliationGovernanceScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _category(*, blocked: bool, unresolved: bool, cosmetic: bool, provisional: bool, not_computable: bool, partial: bool) -> str:
    if not_computable:
        return "NOT_COMPUTABLE"
    if blocked:
        return "BLOCKED"
    if unresolved:
        return "UNRESOLVED_CONFLICT_BURDENED"
    if cosmetic:
        return "COSMETIC_ALIGNMENT_BURDENED"
    if provisional:
        return "PROVISIONAL_BURDENED"
    if partial:
        return "PARTIAL"
    return "RECONCILIATION_GOVERNED"


def build_reconciliation_governance_scorecard() -> ReconciliationGovernanceScorecard:
    conflict = build_state_conflict_report()
    reconciliation = build_reconciliation_report()
    restoration = build_restoration_status_report()
    transitions = build_reconciliation_transition_report()

    not_computable = any(v == "NOT_COMPUTABLE" for v in conflict["conflictStates"].values()) or any(
        v == "NOT_COMPUTABLE" for v in reconciliation["reconciliationStates"].values()
    )
    blocked = any(v in {"BLOCKING_CONFLICT"} for v in conflict["conflictStates"].values()) or any(
        v in {"REPAIR_FORBIDDEN"} for v in reconciliation["reconciliationStates"].values()
    )
    unresolved = any(x["to_state"] == "UNRESOLVED_CONFLICT_ACTIVE" for x in transitions["transitions"])
    cosmetic = any(x["cosmetic_state"] == "COSMETIC_ALIGNMENT_ACTIVE" for x in transitions["cosmeticAlignment"])
    provisional = any(v in {"PROVISIONAL_OR_PENDING"} for v in restoration["restorationStates"].values()) or any(
        x["to_state"] in {"PROVISIONAL_RESTORED", "VALIDATION_REQUIRED"} for x in transitions["transitions"]
    )
    partial = any(v == "CONSISTENCY_PARTIALLY_RESTORED" for v in restoration["restorationStates"].values())

    dimensions = {
        "conflict_class_clarity": "DEGRADED"
        if any(v in {"CONFLICT_UNKNOWN", "NOT_COMPUTABLE"} for v in conflict["conflictStates"].values())
        else "CLEAR",
        "authoritative_source_legitimacy": "AT_RISK"
        if any(x["authority_state"] != "AUTHORITATIVE_SOURCE_SELECTED" for x in reconciliation["authoritativeSources"])
        else "DISCIPLINED",
        "repair_mode_legitimacy": "AT_RISK"
        if any(v in {"REPAIR_FORBIDDEN", "REPAIR_LEGITIMACY_UNKNOWN"} for v in reconciliation["reconciliationStates"].values())
        else "DISCIPLINED",
        "merge_loss_visibility": "ELEVATED"
        if any(x["loss_state"] == "LOSSY_REPAIR_ACTIVE" for x in transitions["lossyRepair"])
        else "LOW",
        "provisional_vs_durable_clarity": "AT_RISK" if provisional else "CLEAR",
        "unresolved_conflict_visibility": "ELEVATED" if unresolved else "LOW",
        "cosmetic_alignment_visibility": "ELEVATED" if cosmetic else "LOW",
        "trust_downgrade_discipline": "ENFORCED" if unresolved or provisional or cosmetic else "PARTIAL",
        "post_repair_validation_quality": "REQUIRED" if provisional else "STABLE",
        "operator_consistency_posture_clarity": "EXPLICIT",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"DEGRADED", "AT_RISK", "ELEVATED", "REQUIRED"})
    blockers.extend(sorted(x["code"] for x in conflict["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in reconciliation["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in restoration["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in transitions["governanceErrors"] if x["severity"] == "ERROR"))
    blockers = sorted(set(blockers))

    evidence = {
        "conflict": [conflict["auditHash"]],
        "reconciliation": [reconciliation["auditHash"]],
        "restoration": [restoration["auditHash"]],
        "transitions": [transitions["auditHash"]],
    }
    category = _category(
        blocked=blocked,
        unresolved=unresolved,
        cosmetic=cosmetic,
        provisional=provisional,
        not_computable=not_computable,
        partial=partial,
    )
    payload = {"dimensions": dimensions, "evidence": evidence, "blockers": blockers, "category": category}
    return ReconciliationGovernanceScorecard(
        artifact_type="ReconciliationGovernanceScorecard.v1",
        artifact_id="reconciliation-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        category=category,
        scorecard_hash=sha256_bytes(dumps_stable(payload).encode("utf-8")),
    )
