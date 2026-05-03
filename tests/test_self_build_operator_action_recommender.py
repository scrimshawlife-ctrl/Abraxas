from __future__ import annotations

from pathlib import Path

from abraxas.registry.self_build_operator_action_recommender import run_self_build_operator_action_recommender


def test_recommender_schema_authority_and_fields() -> None:
    result = run_self_build_operator_action_recommender()
    assert result["schema_version"] == "SelfBuildOperatorActionRecommendations.v1"
    assert result["authority"] == {"mutation": False, "promotion": False, "execution": False, "analysis_only": True}
    if result["status"] == "OK":
        for row in result["actions"]:
            assert {"action_id", "action_type", "target_path", "approval_id", "reason", "confidence", "requires_operator"}.issubset(row.keys())
            assert row["requires_operator"] is True


def test_recommender_deterministic_hash() -> None:
    a = run_self_build_operator_action_recommender()
    b = run_self_build_operator_action_recommender()
    assert a["canonical_hash"] == b["canonical_hash"]


def test_recommender_fail_closed_missing_artifact() -> None:
    target = Path("out/registry/self_build_batch_trends.latest.json")
    backup = Path("out/registry/self_build_batch_trends.latest.json.bak")
    if target.exists():
        backup.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
        target.unlink()
    try:
        result = run_self_build_operator_action_recommender()
        assert result["status"] == "NOT_COMPUTABLE"
    finally:
        if backup.exists():
            target.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
            backup.unlink()
