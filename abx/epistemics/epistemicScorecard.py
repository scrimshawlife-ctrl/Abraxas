from __future__ import annotations

from abx.epistemics.alignmentReports import build_alignment_audit_report
from abx.epistemics.confidenceReports import build_calibration_audit_report
from abx.epistemics.qualityReports import build_epistemic_quality_audit_report
from abx.epistemics.types import EpistemicQualityScorecard
from abx.epistemics.validationReports import build_validation_audit_report
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_epistemic_quality_scorecard() -> EpistemicQualityScorecard:
    validation = build_validation_audit_report()
    calibration = build_calibration_audit_report()
    quality = build_epistemic_quality_audit_report()
    alignment = build_alignment_audit_report()

    dimensions = {
        "validation_surface_clarity": "GOVERNED" if not validation["vocabularyConflicts"] else "PARTIAL",
        "confidence_calibration_coverage": "PARTIAL" if calibration["confidenceStates"]["not_computable"] else "CALIBRATED",
        "epistemic_quality_coverage": "PARTIAL" if quality["qualityClassification"]["NOT_COMPUTABLE"] else "GOVERNED_SUPPORTED",
        "replay_comparison_alignment_quality": "PARTIAL" if alignment["mismatchClassification"]["semantic_drift"] else "GOVERNED",
        "unsupported_confidence_burden": "PARTIAL" if calibration["unsupportedConfidence"] else "GOVERNED",
        "heuristic_output_burden": "PARTIAL" if quality["qualityClassification"]["HEURISTIC"] else "GOVERNED",
        "degraded_suspect_visibility": "GOVERNED",
        "reference_ground_truth_linkage": "MONITORED",
        "operator_uncertainty_legibility": "GOVERNED",
        "legacy_validation_burden": "PARTIAL" if validation["classification"]["legacy_redundant_candidate"] else "GOVERNED",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"PARTIAL", "HEURISTIC", "NOT_COMPUTABLE"})
    evidence = {
        "validation": [validation["auditHash"]],
        "calibration": [calibration["auditHash"]],
        "quality": [quality["auditHash"]],
        "alignment": [alignment["auditHash"]],
        "unsupportedConfidence": calibration["unsupportedConfidence"],
        "semanticDriftComparisons": alignment["mismatchClassification"]["semantic_drift"],
    }
    digest = sha256_bytes(dumps_stable({"dimensions": dimensions, "evidence": evidence, "blockers": blockers}).encode("utf-8"))
    return EpistemicQualityScorecard(
        artifact_type="EpistemicQualityScorecard.v1",
        artifact_id="epistemic-quality-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        scorecard_hash=digest,
    )
