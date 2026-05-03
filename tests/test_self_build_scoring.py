from __future__ import annotations

from abraxas.registry.self_build_scoring import run_self_build_scoring


def test_scoring_schema_and_authority() -> None:
    result = run_self_build_scoring()
    assert result["schema_version"] == "SelfBuildScoring.v1"
    assert result["authority"]["analysis_only"] is True
    assert result["authority"]["mutation"] is False


def test_scoring_contains_expected_keys() -> None:
    result = run_self_build_scoring()
    assert "mutation_scores" in result
    assert "rollback_scores" in result
    assert "top_mutations" in result
    assert "flagged_mutations" in result


def test_scoring_entries_have_totals() -> None:
    result = run_self_build_scoring()
    for row in result["mutation_scores"]:
        assert "total_score" in row
        assert row["classification"] in {"RETAINED", "REVERTED"}
