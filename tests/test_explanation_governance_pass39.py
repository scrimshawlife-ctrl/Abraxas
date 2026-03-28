from __future__ import annotations

from abx.explanation.boundaryReports import build_explanation_boundary_report
from abx.explanation.compressionClassification import classify_compression
from abx.explanation.compressionReports import build_narrative_compression_report
from abx.explanation.explanationScorecard import build_explanation_governance_scorecard
from abx.explanation.explanationScorecardSerialization import serialize_explanation_scorecard
from abx.explanation.honestyClassification import classify_honesty
from abx.explanation.honestyReports import build_interpretive_honesty_report
from abx.explanation.layerClassification import classify_layer
from abx.explanation.transitionReports import build_explanation_transition_report


def test_narrative_compression_determinism_and_classes() -> None:
    report_a = build_narrative_compression_report()
    report_b = build_narrative_compression_report()
    assert report_a == report_b
    assert set(report_a["compressionStates"].values()).issubset(
        {
            "COMPRESSED_WITH_PRESERVATION",
            "COMPRESSED_WITH_NOTED_LOSS",
            "COMPRESSED_WITH_HIDDEN_LOSS_RISK",
            "NO_COMPRESSION_NEEDED",
            "COMPRESSION_UNSAFE",
            "BLOCKED",
            "NOT_COMPUTABLE",
        }
    )
    assert classify_compression(compression_state="COMPRESSED_WITH_PRESERVATION", omitted_context="NONE") == "COMPRESSED_WITH_PRESERVATION"


def test_explanation_boundary_determinism_and_layers() -> None:
    report_a = build_explanation_boundary_report()
    report_b = build_explanation_boundary_report()
    assert report_a == report_b
    assert set(report_a["layerStates"].values()).issuperset({"OBSERVED_LAYER", "INFERRED_LAYER", "BOUNDARY_EXCEEDED", "BOUNDARY_AMBIGUOUS"})
    assert classify_layer(layer_state="INFERRED_LAYER", boundary_state="BOUNDARY_EXCEEDED") == "BOUNDARY_EXCEEDED"


def test_interpretive_honesty_determinism_and_causal_eligibility() -> None:
    report_a = build_interpretive_honesty_report()
    report_b = build_interpretive_honesty_report()
    assert report_a == report_b
    assert set(report_a["honestyStates"].values()).issuperset(
        {"INTERPRETIVELY_HONEST", "INTERPRETIVELY_COMPRESSED_BUT_HONEST", "CAVEAT_OMISSION_RISK", "UNSUPPORTED_EXPLANATORY_JUMP"}
    )
    assert (
        classify_honesty(
            honesty_state="INTERPRETIVELY_HONEST",
            causal_state="CAUSAL_LANGUAGE_USED",
            support_state="INSUFFICIENT",
            omission_state="OMISSION_CLEAR",
        )
        == "CAUSAL_OVERREACH_RISK"
    )


def test_explanation_transition_determinism() -> None:
    report_a = build_explanation_transition_report()
    report_b = build_explanation_transition_report()
    assert report_a == report_b
    assert {x["to_state"] for x in report_a["transitions"]}.issuperset(
        {"COMPRESSION_LOSS_ACTIVE", "CAVEAT_OMISSION_ACTIVE", "BOUNDARY_BLOCK_ACTIVE", "HONESTY_RESTORED"}
    )


def test_explanation_scorecard_determinism_and_blockers() -> None:
    score_a = build_explanation_governance_scorecard()
    score_b = build_explanation_governance_scorecard()
    assert score_a == score_b
    assert score_a.category in {
        "EXPLANATION_GOVERNED",
        "OMISSION_BURDENED",
        "OVERREACH_BURDENED",
        "PARTIAL",
        "BLOCKED",
        "NOT_COMPUTABLE",
    }
    assert "causal_language_discipline" in score_a.blockers
    assert serialize_explanation_scorecard(score_a) == serialize_explanation_scorecard(score_b)


def test_elegance_regression_guards() -> None:
    compression = build_narrative_compression_report()
    boundary = build_explanation_boundary_report()
    honesty = build_interpretive_honesty_report()

    assert len(set(compression["compressionStates"].values())) <= 6
    assert len(set(boundary["layerStates"].values())) <= 7
    assert any(x["layer_state"] == "INFERRED_LAYER" for x in boundary["layers"])
    assert any(x["code"] == "INTERPRETIVE_OVERREACH" for x in honesty["governanceErrors"])
