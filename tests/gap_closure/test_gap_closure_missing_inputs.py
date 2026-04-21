from __future__ import annotations

from pathlib import Path

from abraxas.runes.gap_closure.emit_artifact import emit_artifact
from abraxas.runes.gap_closure.project_run import run_projection_cycle
from abraxas.runes.gap_closure.validate_closure import build_closure_validation_report


def test_gap_closure_missing_inputs_not_computable(tmp_path: Path) -> None:
    run_id = "RUN-GAP-FIRST-0001"
    run_dir = tmp_path / run_id
    cycle = run_projection_cycle(run_id=run_id, mode="sandbox", workspace_only=True, required_input=None)
    emit_artifact(run_dir / "gap_closure_run.json", cycle["run_record"])
    report = build_closure_validation_report(run_id=run_id, run_dir=run_dir, artifact_index=[])
    assert report["status"] == "NOT_COMPUTABLE"
