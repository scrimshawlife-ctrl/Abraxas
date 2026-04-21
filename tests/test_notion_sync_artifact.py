from __future__ import annotations

from scripts.build_notion_sync_artifact import build_sync_artifact


def test_build_sync_artifact_maps_gap_metrics() -> None:
    artifact = build_sync_artifact(
        stub_index={"summary": {"total_stubs": 18}},
        taxonomy={"gap_summary": {"implementation_gap": 9, "policy_block": 7, "intentional_abstract": 2}},
        next_steps={"all_listed_next_steps_completed": False, "all_wave5_ranked_tasks_completed": False},
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
        next_steps={"all_listed_next_steps_completed": False, "all_wave5_ranked_tasks_completed": False},
    )

    assert artifact["status"]["wave"] == "wave_4_completed"
    assert artifact["tasks"][0]["state"] == "completed"
    assert artifact["tasks"][1]["state"] == "completed"


def test_build_sync_artifact_marks_wave5_completed_when_next_steps_closed() -> None:
    artifact = build_sync_artifact(
        stub_index={"summary": {"total_stubs": 4}},
        taxonomy={"gap_summary": {"implementation_gap": 0, "policy_block": 0, "intentional_abstract": 4}},
        next_steps={"all_listed_next_steps_completed": True, "all_wave5_ranked_tasks_completed": True},
    )
    assert artifact["status"]["wave"] == "wave_5_completed"
    wave5_task = next(item for item in artifact["tasks"] if item["id"] == "wave5_ranked_closure")
    assert wave5_task["state"] == "completed"
