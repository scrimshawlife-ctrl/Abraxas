from __future__ import annotations

from abx.identity.coherenceReports import build_referential_coherence_report
from abx.identity.identityReports import build_identity_resolution_report
from abx.identity.persistenceReports import build_entity_persistence_report
from abx.identity.transitionReports import build_identity_transition_report
from abx.identity.types import IdentityGovernanceScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _category(*, blocked: bool, mismatch: bool, duplicate: bool, not_computable: bool, partial: bool) -> str:
    if not_computable:
        return "NOT_COMPUTABLE"
    if blocked:
        return "BLOCKED"
    if mismatch:
        return "MISMATCH_BURDENED"
    if duplicate:
        return "DUPLICATE_BURDENED"
    if partial:
        return "PARTIAL"
    return "IDENTITY_GOVERNED"


def build_identity_governance_scorecard() -> IdentityGovernanceScorecard:
    identity = build_identity_resolution_report()
    persistence = build_entity_persistence_report()
    coherence = build_referential_coherence_report()
    transitions = build_identity_transition_report()

    not_computable = any(v == "NOT_COMPUTABLE" for v in identity["identityStates"].values()) or any(
        v in {"NOT_COMPUTABLE", "CONTINUITY_UNKNOWN"} for v in persistence["persistenceStates"].values()
    )
    blocked = any(v == "BLOCKED" for v in identity["identityStates"].values())
    mismatch = any(x["mismatch_state"] == "REFERENCE_MISMATCH_ACTIVE" for x in transitions["mismatch"])
    duplicate = any(v in {"DUPLICATE_ENTITY_SUSPECTED", "DUPLICATE_ENTITY_CONFIRMED"} for v in coherence["coherenceStates"].values())
    partial = any(v in {"ALIAS_RESOLVED", "MERGE_ACTIVE_COHERENT", "SPLIT_ACTIVE_COHERENT", "REMAPPED_CANONICAL_IDENTITY"} for v in list(identity["identityStates"].values()) + list(coherence["coherenceStates"].values()) + list(persistence["persistenceStates"].values()))

    dimensions = {
        "canonical_identity_clarity": "DEGRADED" if mismatch else "CLEAR",
        "alias_deprecated_distinction_quality": "AT_RISK"
        if any(x["alias_state"] == "DEPRECATED_IDENTIFIER_ACTIVE" for x in coherence["alias"])
        else "DISCIPLINED",
        "persistence_continuity_quality": "AT_RISK"
        if any(v in {"IDENTITY_BREAK", "IMPORTED_IDENTITY_SHADOW"} for v in persistence["persistenceStates"].values())
        else "DISCIPLINED",
        "merge_split_legitimacy_quality": "AT_RISK"
        if any(x["merge_state"] == "MERGE_ILLEGITIMATE" for x in coherence["merge"]) or any(x["split_state"] == "SPLIT_ILLEGITIMATE" for x in coherence["split"])
        else "DISCIPLINED",
        "duplicate_entity_visibility": "ELEVATED" if duplicate else "LOW",
        "reference_mismatch_visibility": "ELEVATED" if mismatch else "LOW",
        "remap_discipline": "REQUIRED"
        if any(x["mismatch_state"] == "REMAP_REQUIRED" for x in transitions["mismatch"])
        else "STABLE",
        "cross_system_coherence_quality": "AT_RISK"
        if any(x["downstream_state"] == "DOWNSTREAM_CONFLICT" for x in coherence["coherence"])
        else "DISCIPLINED",
        "trust_downgrade_discipline": "ENFORCED" if mismatch or duplicate else "PARTIAL",
        "operator_referential_posture_clarity": "EXPLICIT",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"DEGRADED", "AT_RISK", "ELEVATED", "REQUIRED"})
    blockers.extend(sorted(x["code"] for x in identity["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in persistence["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in coherence["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in transitions["governanceErrors"] if x["severity"] == "ERROR"))
    blockers = sorted(set(blockers))

    evidence = {
        "identity": [identity["auditHash"]],
        "persistence": [persistence["auditHash"]],
        "coherence": [coherence["auditHash"]],
        "transitions": [transitions["auditHash"]],
    }
    category = _category(
        blocked=blocked,
        mismatch=mismatch,
        duplicate=duplicate,
        not_computable=not_computable,
        partial=partial,
    )
    payload = {"dimensions": dimensions, "evidence": evidence, "blockers": blockers, "category": category}
    return IdentityGovernanceScorecard(
        artifact_type="IdentityGovernanceScorecard.v1",
        artifact_id="identity-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        category=category,
        scorecard_hash=sha256_bytes(dumps_stable(payload).encode("utf-8")),
    )
