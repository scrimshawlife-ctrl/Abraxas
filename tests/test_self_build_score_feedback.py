from __future__ import annotations

from abraxas.registry.self_build_score_feedback import run_self_build_score_feedback


def test_feedback_schema_authority() -> None:
    result = run_self_build_score_feedback()
    assert result["schema_version"] == "SelfBuildScoreFeedback.v1"
    assert result["authority"] == {
        "mutation": False,
        "promotion": False,
        "execution": False,
        "analysis_only": True,
    }


def test_feedback_has_ranked_and_annotations() -> None:
    result = run_self_build_score_feedback()
    assert "ranked_targets" in result
    assert "flagged_targets" in result
    assert "blocked_targets" in result


def test_feedback_deterministic_hash_shape() -> None:
    a = run_self_build_score_feedback()
    b = run_self_build_score_feedback()
    assert isinstance(a.get("canonical_hash"), str)
    assert a["canonical_hash"] == b["canonical_hash"]
