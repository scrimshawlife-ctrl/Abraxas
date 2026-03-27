from __future__ import annotations

from scripts.build_notion_sync_artifact import build_sync_artifact


def test_build_sync_artifact_maps_gap_metrics() -> None:
    artifact = build_sync_artifact(
        stub_index={"summary": {"total_stubs": 18}},
        taxonomy={"gap_summary": {"implementation_gap": 9, "policy_block": 7, "intentional_abstract": 2}},
    )

    assert artifact["generated_at"] == "auto"
    assert artifact["status"]["wave"] == "wave_4_in_progress"
    assert artifact["metrics"] == {
        "total_stubs": 18,
        "implementation_gap": 9,
        "policy_block": 7,
        "intentional_abstract": 2,
    }
    assert artifact["tasks"][0]["id"] == "operator_gap_burn_down"
    assert artifact["tasks"][0]["state"] == "in_progress"


def test_build_sync_artifact_marks_wave_completed_without_actionable_gaps() -> None:
    artifact = build_sync_artifact(
        stub_index={"summary": {"total_stubs": 4}},
        taxonomy={"gap_summary": {"implementation_gap": 0, "policy_block": 0, "intentional_abstract": 4}},
    )

    assert artifact["status"]["wave"] == "wave_4_completed"
    assert artifact["tasks"][0]["state"] == "completed"
    assert artifact["tasks"][1]["state"] == "completed"
