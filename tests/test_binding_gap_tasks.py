from __future__ import annotations

from abraxas.registry.binding_gap_tasks import run_binding_gap_tasks


def test_gap_tasks_runs() -> None:
    result = run_binding_gap_tasks()
    assert result["schema_version"] == "BindingGapTasks.v1"
    assert "tasks" in result


def test_gap_tasks_deterministic() -> None:
    first = run_binding_gap_tasks()
    second = run_binding_gap_tasks()
    assert first["canonical_hash"] == second["canonical_hash"]
