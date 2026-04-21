import json
import subprocess
import sys
from pathlib import Path


def test_run_notion_next_steps_emits_wave5_focus(tmp_path: Path):
    out = tmp_path / "notion_next_steps.json"
    cp = subprocess.run(
        [
            sys.executable,
            "scripts/run_notion_next_steps.py",
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 0
    payload = json.loads(out.read_text(encoding="utf-8"))

    assert payload["version"] == "notion_next_steps.v0.1"
    assert payload["current_wave"] == "wave_5_completed"
    assert payload["recommended_focus"] == "closure_review"
    assert payload["wave_5_ranked_tasks"]
    assert payload["repo_grounded_tasks"]
    assert payload["all_listed_next_steps_completed"] is True
    assert payload["remaining_task_ids"] == []
    assert payload["remaining_repo_grounded_tasks"] == []
    assert len(payload["completed_repo_grounded_tasks"]) == len(payload["repo_grounded_tasks"])
    assert all(item["state"] == "completed" for item in payload["task_status"])
    assert payload["all_wave5_ranked_tasks_completed"] is True
    assert payload["remaining_wave5_task_ids"] == []
    assert all(item["state"] == "completed" for item in payload["wave_5_task_status"])
