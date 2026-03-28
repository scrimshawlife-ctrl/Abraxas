from __future__ import annotations

from abx.semantic.compatibilityReports import build_schema_evolution_report
from abx.semantic.meaningReports import build_meaning_preservation_report
from abx.semantic.semanticReports import build_semantic_drift_report
from abx.semantic.transitionReports import build_semantic_transition_report
from abx.semantic.types import SemanticGovernanceScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _category(*, blocked: bool, break_active: bool, risk_burdened: bool, not_computable: bool, partial: bool) -> str:
    if not_computable:
        return "NOT_COMPUTABLE"
    if blocked:
        return "BLOCKED"
    if break_active:
        return "SEMANTIC_BREAK_BURDENED"
    if risk_burdened:
        return "REINTERPRETATION_RISK_BURDENED"
    if partial:
        return "PARTIAL"
    return "SEMANTIC_GOVERNED"


def build_semantic_governance_scorecard() -> SemanticGovernanceScorecard:
    semantic = build_semantic_drift_report()
    schema = build_schema_evolution_report()
    meaning = build_meaning_preservation_report()
    transitions = build_semantic_transition_report()

    not_computable = any(v == "NOT_COMPUTABLE" for v in semantic["semanticStates"].values()) or any(
        x["compatibility_state"] == "NOT_COMPUTABLE" for x in schema["compatibility"]
    )
    blocked = any(x["to_state"] == "BLOCKED" for x in transitions["transitions"])
    break_active = any(v in {"SEMANTIC_BREAK", "SEMANTIC_DRIFT_DETECTED"} for v in semantic["semanticStates"].values())
    risk_burdened = any(v in {"MIGRATION_REQUIRED", "REINTERPRETATION_RISK"} for v in meaning["meaningStates"].values())
    partial = any(x["compatibility_state"] == "BACKWARD_PARSEABLE_ONLY" for x in schema["compatibility"])

    dimensions = {
        "meaning_identity_clarity": "NOT_COMPUTABLE_PRESENT" if not_computable else "EXPLICIT",
        "semantic_drift_visibility": "VISIBLE",
        "structural_vs_semantic_compatibility_quality": "GAP_PRESENT"
        if any(x["compatibility_state"] == "STRUCTURALLY_COMPATIBLE_BUT_SEMANTICALLY_SHIFTED" for x in schema["compatibility"])
        else "CLEAR",
        "migration_meaning_preservation_quality": "AT_RISK" if risk_burdened else "DISCIPLINED",
        "alias_deprecation_hygiene": "DEGRADING"
        if any(v in {"SEMANTIC_ALIAS_ACTIVE", "SEMANTIC_DEPRECATION_ACTIVE"} for v in semantic["semanticStates"].values())
        else "STABLE",
        "reinterpretation_risk_burden": "ELEVATED" if risk_burdened else "LOW",
        "semantic_break_visibility": "VISIBLE" if break_active else "LOW",
        "downstream_translation_readiness": "REQUIRED"
        if any(x["translation_required"] == "YES" for x in meaning["meaning"])
        else "CLEAR",
        "trust_downgrade_discipline": "ENFORCED" if blocked or break_active else "PARTIAL",
        "operator_semantic_posture_clarity": "EXPLICIT",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"NOT_COMPUTABLE_PRESENT", "GAP_PRESENT", "AT_RISK", "ELEVATED", "REQUIRED"})
    blockers.extend(sorted(x["code"] for x in semantic["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in schema["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in meaning["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in transitions["governanceErrors"] if x["severity"] == "ERROR"))
    blockers = sorted(set(blockers))

    evidence = {
        "semantic": [semantic["auditHash"]],
        "schema": [schema["auditHash"]],
        "meaning": [meaning["auditHash"]],
        "transitions": [transitions["auditHash"]],
    }
    category = _category(
        blocked=blocked,
        break_active=break_active,
        risk_burdened=risk_burdened,
        not_computable=not_computable,
        partial=partial,
    )
    payload = {"dimensions": dimensions, "evidence": evidence, "blockers": blockers, "category": category}
    return SemanticGovernanceScorecard(
        artifact_type="SemanticGovernanceScorecard.v1",
        artifact_id="semantic-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        category=category,
        scorecard_hash=sha256_bytes(dumps_stable(payload).encode("utf-8")),
    )
