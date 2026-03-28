from __future__ import annotations

from abx.semantic.compatibilityClassification import classify_compatibility
from abx.semantic.compatibilityReports import build_schema_evolution_report
from abx.semantic.meaningReports import build_meaning_preservation_report
from abx.semantic.migrationClassification import classify_meaning_preservation
from abx.semantic.semanticClassification import classify_semantic_drift
from abx.semantic.semanticReports import build_semantic_drift_report
from abx.semantic.semanticScorecard import build_semantic_governance_scorecard
from abx.semantic.semanticScorecardSerialization import serialize_semantic_scorecard
from abx.semantic.transitionReports import build_semantic_transition_report


def test_semantic_drift_determinism_and_classes() -> None:
    report_a = build_semantic_drift_report()
    report_b = build_semantic_drift_report()
    assert report_a == report_b
    assert set(report_a["semanticStates"].values()).issubset(
        {
            "MEANING_PRESERVED",
            "SEMANTIC_DRIFT_DETECTED",
            "SEMANTIC_ALIAS_ACTIVE",
            "SEMANTIC_DEPRECATION_ACTIVE",
            "SEMANTIC_UNKNOWN",
            "SEMANTIC_BREAK",
            "NOT_COMPUTABLE",
        }
    )
    assert classify_semantic_drift(drift_state="SEMANTIC_DRIFT_DETECTED", drift_kind="INTERPRETIVE") == "SEMANTIC_DRIFT_DETECTED"


def test_schema_evolution_determinism_and_compatibility() -> None:
    report_a = build_schema_evolution_report()
    report_b = build_schema_evolution_report()
    assert report_a == report_b
    states = {x["compatibility_state"] for x in report_a["compatibility"]}
    assert states.issuperset({"BACKWARD_COMPATIBLE", "STRUCTURALLY_COMPATIBLE_BUT_SEMANTICALLY_SHIFTED", "BACKWARD_PARSEABLE_ONLY", "NOT_COMPUTABLE"})
    assert classify_compatibility(
        structural_compatibility="STRUCTURALLY_COMPATIBLE",
        semantic_compatibility="STRUCTURALLY_COMPATIBLE_BUT_SEMANTICALLY_SHIFTED",
    ) == "STRUCTURALLY_COMPATIBLE_BUT_SEMANTICALLY_SHIFTED"


def test_meaning_preservation_determinism_and_migration_states() -> None:
    report_a = build_meaning_preservation_report()
    report_b = build_meaning_preservation_report()
    assert report_a == report_b
    assert set(report_a["meaningStates"].values()).issuperset({"MEANING_PRESERVED", "MIGRATION_REQUIRED", "SEMANTIC_BREAK"})
    assert (
        classify_meaning_preservation(
            preservation_state="MEANING_PRESERVED_VIA_MIGRATION",
            migration_state="MIGRATION_COMPLETE",
            translation_required="NO",
        )
        == "MEANING_PRESERVED"
    )


def test_semantic_transition_determinism() -> None:
    report_a = build_semantic_transition_report()
    report_b = build_semantic_transition_report()
    assert report_a == report_b
    assert {x["to_state"] for x in report_a["transitions"]}.issuperset(
        {"STRUCTURALLY_COMPATIBLE_BUT_SEMANTICALLY_SHIFTED", "ALIAS_DRIFT_DETECTED", "BLOCKED", "MEANING_RESTORED"}
    )


def test_semantic_scorecard_determinism_and_blockers() -> None:
    score_a = build_semantic_governance_scorecard()
    score_b = build_semantic_governance_scorecard()
    assert score_a == score_b
    assert score_a.category in {
        "SEMANTIC_GOVERNED",
        "REINTERPRETATION_RISK_BURDENED",
        "SEMANTIC_BREAK_BURDENED",
        "BLOCKED",
        "PARTIAL",
        "NOT_COMPUTABLE",
    }
    assert "meaning_identity_clarity" in score_a.blockers
    assert serialize_semantic_scorecard(score_a) == serialize_semantic_scorecard(score_b)


def test_elegance_regression_guards() -> None:
    semantic = build_semantic_drift_report()
    schema = build_schema_evolution_report()
    meaning = build_meaning_preservation_report()

    assert len(set(semantic["semanticStates"].values())) <= 8
    assert len({x["compatibility_state"] for x in schema["compatibility"]}) <= 6
    assert any(x["compatibility_state"] == "BACKWARD_PARSEABLE_ONLY" for x in schema["compatibility"])
    assert any(x["code"] == "MEANING_PRESERVATION_FAIL" for x in meaning["governanceErrors"])
