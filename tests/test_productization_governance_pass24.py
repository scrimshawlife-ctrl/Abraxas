from __future__ import annotations

from abx.productization.audienceCoverage import classify_audience_legibility
from abx.productization.audienceEntrypoints import detect_audience_terminology_drift
from abx.productization.audienceReports import build_audience_legibility_audit_report
from abx.productization.outputReports import build_output_boundedness_audit_report, classify_output_boundedness
from abx.productization.packageCompatibility import (
    classify_package_compatibility,
    detect_redundant_package_dialects,
)
from abx.productization.packageReports import build_packaging_audit_report
from abx.productization.productClassification import (
    classify_product_surfaces,
    detect_duplicate_product_surfaces,
)
from abx.productization.productReports import build_product_surface_audit_report
from abx.productization.productScorecard import build_productization_governance_scorecard


def test_product_surface_governance_stability() -> None:
    assert classify_product_surfaces() == classify_product_surfaces()
    assert detect_duplicate_product_surfaces() == []
    report = build_product_surface_audit_report()
    assert report == build_product_surface_audit_report()
    assert report["classification"]["canonical_external"]


def test_packaging_contract_stability() -> None:
    assert classify_package_compatibility() == classify_package_compatibility()
    assert detect_redundant_package_dialects() == []
    report = build_packaging_audit_report()
    assert report == build_packaging_audit_report()
    assert report["compatibility"]["partial"]


def test_audience_legibility_stability() -> None:
    assert classify_audience_legibility() == classify_audience_legibility()
    assert detect_audience_terminology_drift() == []
    report = build_audience_legibility_audit_report()
    assert report == build_audience_legibility_audit_report()
    assert report["coverage"]["fully_legible"]


def test_output_boundedness_stability() -> None:
    assert classify_output_boundedness() == classify_output_boundedness()
    report = build_output_boundedness_audit_report()
    assert report == build_output_boundedness_audit_report()
    assert report["boundednessClassification"]["caution_required"]


def test_productization_scorecard_determinism_and_blockers() -> None:
    a = build_productization_governance_scorecard()
    b = build_productization_governance_scorecard()
    assert a.__dict__ == b.__dict__
    assert "packaging_contract_quality" in a.blockers
    assert "external_output_interpretability" in a.blockers
