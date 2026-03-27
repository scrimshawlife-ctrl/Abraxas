from __future__ import annotations

from abx.meta.canonReports import build_canon_audit_report
from abx.meta.canonResolutionReports import build_canon_conflict_audit_report
from abx.meta.changeReports import build_governance_change_audit_report
from abx.meta.metaScorecardSerialization import serialize_meta_governance_scorecard
from abx.meta.stewardshipReports import build_stewardship_audit_report
from abx.meta.types import MetaGovernanceScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_meta_governance_scorecard() -> MetaGovernanceScorecard:
    canon = build_canon_audit_report()
    change = build_governance_change_audit_report()
    steward = build_stewardship_audit_report()
    conflict = build_canon_conflict_audit_report()

    dimensions = {
        "canon_surface_clarity": "GOVERNED" if not canon["taxonomyDrift"] else "PARTIAL",
        "governance_change_traceability": "PARTIAL" if change["hiddenMetaChange"] else "GOVERNED",
        "self_modification_discipline": "GOVERNED" if change["selfModification"] else "NOT_COMPUTABLE",
        "stewardship_clarity": "PARTIAL" if steward["hiddenAuthority"] else "STEWARDED",
        "supersession_conflict_visibility": "PARTIAL" if conflict["unresolvedDrift"] else "GOVERNED",
        "canon_clutter_burden": "PARTIAL" if canon["classification"]["shadow_candidate"] else "GOVERNED",
        "shadow_meta_experiment_containment": "PARTIAL" if change["classification"]["shadow_meta_experiment"] else "GOVERNED",
        "rule_compression_quality": "GOVERNED" if conflict["classification"]["merged_compressed"] else "PARTIAL",
        "long_arc_governance_coherence": "MONITORED",
        "operator_legibility_for_meta_change": "MONITORED",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"PARTIAL", "NOT_COMPUTABLE", "CONFLICTED"})
    evidence = {
        "canon": [canon["auditHash"]],
        "change": [change["auditHash"]],
        "steward": [steward["auditHash"]],
        "conflict": [conflict["auditHash"]],
        "shadow": change["classification"]["shadow_meta_experiment"],
        "unresolved": [x["conflictId"] for x in conflict["unresolvedDrift"]],
    }
    digest = sha256_bytes(dumps_stable({"dimensions": dimensions, "evidence": evidence, "blockers": blockers}).encode("utf-8"))
    return MetaGovernanceScorecard(
        artifact_type="MetaGovernanceScorecard.v1",
        artifact_id="meta-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        scorecard_hash=digest,
    )


def render_meta_governance_scorecard() -> str:
    return serialize_meta_governance_scorecard(build_meta_governance_scorecard())
