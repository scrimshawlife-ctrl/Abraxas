from __future__ import annotations

from abx.epistemics.alignmentReports import (
    build_alignment_audit_report,
    classify_alignment_mismatches,
    classify_alignment_modes,
)
from abx.epistemics.confidenceClassification import (
    classify_confidence_states,
    detect_unsupported_confidence_drift,
)
from abx.epistemics.confidenceReports import build_calibration_audit_report
from abx.epistemics.epistemicScorecard import build_epistemic_quality_scorecard
from abx.epistemics.qualityClassification import (
    classify_epistemic_quality_states,
    detect_inconsistent_quality_terminology,
)
from abx.epistemics.qualityReports import build_epistemic_quality_audit_report
from abx.epistemics.validationClassification import (
    classify_validation_surfaces,
    detect_duplicate_epistemic_vocabulary,
)
from abx.epistemics.validationReports import build_validation_audit_report


def test_validation_surface_classification_and_report_determinism() -> None:
    assert classify_validation_surfaces() == classify_validation_surfaces()
    assert detect_duplicate_epistemic_vocabulary() == []
    a = build_validation_audit_report()
    b = build_validation_audit_report()
    assert a == b
    assert a["classification"]["authoritative"]


def test_confidence_calibration_classification_stability() -> None:
    assert classify_confidence_states() == classify_confidence_states()
    unsupported = detect_unsupported_confidence_drift()
    assert unsupported == detect_unsupported_confidence_drift()
    assert len(unsupported) >= 1
    report = build_calibration_audit_report()
    assert report == build_calibration_audit_report()


def test_epistemic_quality_classification_and_linkage_stability() -> None:
    assert classify_epistemic_quality_states() == classify_epistemic_quality_states()
    assert detect_inconsistent_quality_terminology() == []
    report = build_epistemic_quality_audit_report()
    assert report == build_epistemic_quality_audit_report()
    assert report["qualityClassification"]["SUSPECT"]


def test_alignment_classification_and_report_stability() -> None:
    assert classify_alignment_modes() == classify_alignment_modes()
    assert classify_alignment_mismatches() == classify_alignment_mismatches()
    report = build_alignment_audit_report()
    assert report == build_alignment_audit_report()
    assert report["mismatchClassification"]["semantic_drift"]


def test_epistemic_scorecard_determinism_and_blockers() -> None:
    a = build_epistemic_quality_scorecard()
    b = build_epistemic_quality_scorecard()
    assert a.__dict__ == b.__dict__
    assert "unsupported_confidence_burden" in a.blockers
    assert "replay_comparison_alignment_quality" in a.blockers
