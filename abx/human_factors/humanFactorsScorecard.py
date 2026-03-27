from __future__ import annotations

from abx.human_factors.actionReports import build_warning_action_audit_report
from abx.human_factors.cognitiveReports import build_cognitive_load_audit_report
from abx.human_factors.interactionReports import build_interaction_audit_report
from abx.human_factors.pathReports import build_operator_path_audit_report
from abx.human_factors.types import UXHumanFactorsScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_human_factors_scorecard() -> UXHumanFactorsScorecard:
    interaction = build_interaction_audit_report()
    cognitive = build_cognitive_load_audit_report()
    warning = build_warning_action_audit_report()
    paths = build_operator_path_audit_report()

    dimensions = {
        "interaction_surface_clarity": "GOVERNED" if not interaction["duplicates"] else "PARTIAL",
        "redundancy_burden": "PARTIAL" if interaction["classification"]["legacy_deprecated_candidate"] else "GOVERNED",
        "warning_action_clarity": "GOVERNED" if not warning["warningVocabularyConflicts"] else "PARTIAL",
        "prioritization_quality": "GOVERNED",
        "operator_path_clarity": "PARTIAL" if paths["classification"]["legacy"] else "GOVERNED",
        "degraded_incident_usability": "GOVERNED",
        "drilldown_layering_quality": "PARTIAL" if warning["redundantSummaries"] else "GOVERNED",
        "terminology_consistency": "GOVERNED" if not warning["actionGrammarDrift"] else "PARTIAL",
        "cognitive_overload_risk_visibility": "OVERLOADED" if cognitive["urgencyClassification"]["critical"] else "MONITORED",
        "training_reentry_friendliness": "MONITORED",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"PARTIAL", "HEURISTIC", "NOT_COMPUTABLE", "OVERLOADED"})
    evidence = {
        "interaction": [interaction["auditHash"]],
        "cognitive": [cognitive["auditHash"]],
        "warning": [warning["auditHash"]],
        "paths": [paths["auditHash"]],
        "redundantSummaries": warning["redundantSummaries"],
        "legacyPaths": paths["classification"]["legacy"],
    }
    digest = sha256_bytes(dumps_stable({"dimensions": dimensions, "evidence": evidence, "blockers": blockers}).encode("utf-8"))
    return UXHumanFactorsScorecard(
        artifact_type="UXHumanFactorsScorecard.v1",
        artifact_id="ux-human-factors-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        scorecard_hash=digest,
    )
