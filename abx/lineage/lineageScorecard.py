from __future__ import annotations

from abx.lineage.lineageReports import build_lineage_report
from abx.lineage.mutationReports import build_mutation_report
from abx.lineage.provenanceReports import build_provenance_report
from abx.lineage.transitionReports import build_provenance_transition_report
from abx.lineage.types import LineageGovernanceScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _category(*, blocked: bool, broken: bool, stale: bool, unauthorized: bool, partial: bool, not_computable: bool) -> str:
    if not_computable:
        return "NOT_COMPUTABLE"
    if blocked:
        return "BLOCKED"
    if broken or unauthorized:
        return "PROVENANCE_BROKEN_BURDENED"
    if stale:
        return "STALE_DERIVED_BURDENED"
    if partial:
        return "PARTIAL"
    return "LINEAGE_GOVERNED"


def build_lineage_governance_scorecard() -> LineageGovernanceScorecard:
    lineage = build_lineage_report()
    provenance = build_provenance_report()
    mutation = build_mutation_report()
    transitions = build_provenance_transition_report()

    broken = any(x["provenance_state"] == "PROVENANCE_BROKEN" for x in provenance["provenance"])
    stale = any(x["stale_state"] == "YES" for x in provenance["derivations"])
    unauthorized = any(x["unauthorized_state"] == "UNAUTHORIZED_MUTATION" for x in transitions["unauthorized"])
    blocked = any(v == "BLOCKED" for v in mutation["mutationStates"].values())
    partial = any(x["provenance_state"] == "PROVENANCE_PARTIAL" for x in provenance["provenance"])
    not_computable = any(v == "NOT_COMPUTABLE" for v in lineage["lineageStates"].values()) or any(
        x["provenance_state"] == "NOT_COMPUTABLE" for x in provenance["provenance"]
    )

    dimensions = {
        "source_traceability_clarity": "NOT_COMPUTABLE_PRESENT" if not_computable else "EXPLICIT",
        "derivation_validity_quality": "BROKEN_PRESENT" if broken else ("STALE_PRESENT" if stale else "VALID"),
        "mutation_legitimacy_quality": "UNAUTHORIZED_PRESENT"
        if unauthorized
        else ("BLOCKED_PRESENT" if blocked else "LEGITIMATE"),
        "replayability_posture": "PARTIAL"
        if any(x["replay_state"] == "NON_REPLAYABLE_STATE" for x in transitions["replayability"])
        else "REPLAYABLE",
        "stale_derived_burden": "ELEVATED" if stale else "LOW",
        "provenance_break_visibility": "VISIBLE",
        "unauthorized_mutation_visibility": "VISIBLE" if unauthorized else "LOW",
        "trust_downgrade_discipline": "ENFORCED" if unauthorized or blocked else "PARTIAL",
        "refresh_rederivation_hygiene": "ELEVATED" if stale or partial else "LOW",
        "operator_state_trust_clarity": "EXPLICIT",
    }
    blockers = sorted(
        k
        for k, v in dimensions.items()
        if v in {"BROKEN_PRESENT", "UNAUTHORIZED_PRESENT", "ELEVATED", "BLOCKED_PRESENT", "NOT_COMPUTABLE_PRESENT"}
    )
    blockers.extend(sorted(error["code"] for error in lineage["governanceErrors"] if error["severity"] == "ERROR"))
    blockers.extend(sorted(error["code"] for error in provenance["governanceErrors"] if error["severity"] == "ERROR"))
    blockers.extend(sorted(error["code"] for error in mutation["governanceErrors"] if error["severity"] == "ERROR"))
    blockers.extend(sorted(error["code"] for error in transitions["governanceErrors"] if error["severity"] == "ERROR"))
    blockers = sorted(set(blockers))
    evidence = {
        "lineage": [lineage["auditHash"]],
        "provenance": [provenance["auditHash"]],
        "mutation": [mutation["auditHash"]],
        "transitions": [transitions["auditHash"]],
    }
    category = _category(
        blocked=blocked,
        broken=broken,
        stale=stale,
        unauthorized=unauthorized,
        partial=partial,
        not_computable=not_computable,
    )
    scorecard_hash = sha256_bytes(dumps_stable({"dimensions": dimensions, "evidence": evidence, "blockers": blockers, "category": category}).encode("utf-8"))
    return LineageGovernanceScorecard(
        artifact_type="LineageGovernanceScorecard.v1",
        artifact_id="lineage-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        category=category,
        scorecard_hash=scorecard_hash,
    )
