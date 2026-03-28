from __future__ import annotations

from abx.explanation.boundaryReports import build_explanation_boundary_report
from abx.explanation.compressionReports import build_narrative_compression_report
from abx.explanation.honestyReports import build_interpretive_honesty_report
from abx.explanation.transitionReports import build_explanation_transition_report
from abx.explanation.types import ExplanationGovernanceScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _category(*, blocked: bool, overreach: bool, omission_burden: bool, not_computable: bool, partial: bool) -> str:
    if not_computable:
        return "NOT_COMPUTABLE"
    if blocked:
        return "BLOCKED"
    if overreach:
        return "OVERREACH_BURDENED"
    if omission_burden:
        return "OMISSION_BURDENED"
    if partial:
        return "PARTIAL"
    return "EXPLANATION_GOVERNED"


def build_explanation_governance_scorecard() -> ExplanationGovernanceScorecard:
    compression = build_narrative_compression_report()
    boundary = build_explanation_boundary_report()
    honesty = build_interpretive_honesty_report()
    transitions = build_explanation_transition_report()

    not_computable = any(v == "NOT_COMPUTABLE" for v in compression["compressionStates"].values()) or any(
        x["boundary_state"] == "NOT_COMPUTABLE" for x in boundary["boundaries"]
    )
    blocked = any(x["to_state"] == "BOUNDARY_BLOCK_ACTIVE" for x in transitions["transitions"])
    overreach = any(v in {"UNSUPPORTED_EXPLANATORY_JUMP", "CAUSAL_OVERREACH_RISK"} for v in honesty["honestyStates"].values())
    omission_burden = any(v in {"CAVEAT_OMISSION_RISK", "COMPRESSED_WITH_HIDDEN_LOSS_RISK"} for v in honesty["honestyStates"].values()) or any(
        v == "COMPRESSED_WITH_HIDDEN_LOSS_RISK" for v in compression["compressionStates"].values()
    )
    partial = any(v == "COMPRESSED_WITH_NOTED_LOSS" for v in compression["compressionStates"].values())

    dimensions = {
        "compression_preservation_quality": "AT_RISK" if omission_burden else "DISCIPLINED",
        "explanation_layer_clarity": "DEGRADED"
        if any(x["boundary_state"] in {"BOUNDARY_EXCEEDED", "BOUNDARY_AMBIGUOUS"} for x in boundary["boundaries"])
        else "CLEAR",
        "causal_language_discipline": "VIOLATED" if overreach else "DISCIPLINED",
        "omission_risk_visibility": "VISIBLE" if omission_burden else "LOW",
        "speculation_boundary_hygiene": "AT_RISK"
        if any(v in {"SPECULATIVE_LAYER", "BOUNDARY_AMBIGUOUS"} for v in boundary["layerStates"].values())
        else "CLEAR",
        "caveat_preservation_quality": "AT_RISK"
        if any(x["omission_state"] == "CAVEAT_OMISSION_RISK" for x in honesty["omission"])
        else "DISCIPLINED",
        "explanation_refresh_discipline": "REQUIRED"
        if any(x["to_state"] in {"COMPRESSION_LOSS_ACTIVE", "CAVEAT_OMISSION_ACTIVE"} for x in transitions["transitions"])
        else "CLEAR",
        "overreach_burden": "ELEVATED" if overreach else "LOW",
        "trust_downgrade_discipline": "ENFORCED" if blocked or overreach else "PARTIAL",
        "operator_explanation_posture_clarity": "EXPLICIT",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"AT_RISK", "VIOLATED", "REQUIRED", "ELEVATED", "DEGRADED"})
    blockers.extend(sorted(x["code"] for x in compression["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in boundary["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in honesty["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in transitions["governanceErrors"] if x["severity"] == "ERROR"))
    blockers = sorted(set(blockers))

    evidence = {
        "compression": [compression["auditHash"]],
        "boundary": [boundary["auditHash"]],
        "honesty": [honesty["auditHash"]],
        "transitions": [transitions["auditHash"]],
    }

    category = _category(
        blocked=blocked,
        overreach=overreach,
        omission_burden=omission_burden,
        not_computable=not_computable,
        partial=partial,
    )
    payload = {"dimensions": dimensions, "evidence": evidence, "blockers": blockers, "category": category}
    return ExplanationGovernanceScorecard(
        artifact_type="ExplanationGovernanceScorecard.v1",
        artifact_id="explanation-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        category=category,
        scorecard_hash=sha256_bytes(dumps_stable(payload).encode("utf-8")),
    )
