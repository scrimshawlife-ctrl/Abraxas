from __future__ import annotations

from pathlib import Path

from abraxas.runes.gap_closure.runtime import build_gap_closure_cycle, write_canonical_json
from abraxas.runes.gap_closure.validator import validate_gap_closure_artifacts


def _run_artifacts(base: Path, run_id: str, required_input: dict[str, object] | None) -> tuple[dict, dict, dict]:
    run_dir = base / "artifacts_seal" / "runs" / run_id
    cycle = build_gap_closure_cycle(
        run_id=run_id,
        mode="sandbox",
        workspace_only=True,
        required_input=required_input,
    )
    run_path = run_dir / "gap_closure_run.json"
    projection_path = run_dir / "live_run_projection.json"
    report_path = run_dir / "closure_validation_report.json"
    run_hash = write_canonical_json(run_path, cycle["run_record"])
    projection_hash = write_canonical_json(projection_path, cycle["projection"])
    report_hash = write_canonical_json(
        report_path,
        {
            "schema_version": "closure_validation_report.v1",
            "run_id": run_id,
            "status": "PARTIAL",
            "promotion_decision": "HOLD",
            "reason": "validation_pending_artifact_index",
            "authority_boundary": "projection cannot alter canon status",
        },
    )
    artifact_index = [
        {
            "schema_version": "gap_closure_artifact.v1",
            "run_id": run_id,
            "artifact_path": run_path.as_posix(),
            "artifact_hash": run_hash,
            "provenance": cycle["run_record"]["provenance"],
            "input_hash": cycle["input_hash"],
        },
        {
            "schema_version": "gap_closure_artifact.v1",
            "run_id": run_id,
            "artifact_path": projection_path.as_posix(),
            "artifact_hash": projection_hash,
            "provenance": cycle["run_record"]["provenance"],
            "input_hash": cycle["input_hash"],
        },
        {
            "schema_version": "gap_closure_artifact.v1",
            "run_id": run_id,
            "artifact_path": report_path.as_posix(),
            "artifact_hash": report_hash,
            "provenance": cycle["run_record"]["provenance"],
            "input_hash": cycle["input_hash"],
        },
    ]
    report = validate_gap_closure_artifacts(run_id=run_id, run_dir=run_dir, artifact_index=artifact_index)
    return cycle, {"artifact_index": artifact_index}, report


def test_determinism_same_input_same_hash() -> None:
    cycle_a = build_gap_closure_cycle(
        run_id="RUN-GAP-FIRST-0001",
        mode="sandbox",
        workspace_only=True,
        required_input={"input_state": "present", "source": "default"},
    )
    cycle_b = build_gap_closure_cycle(
        run_id="RUN-GAP-FIRST-0001",
        mode="sandbox",
        workspace_only=True,
        required_input={"input_state": "present", "source": "default"},
    )
    assert cycle_a["input_hash"] == cycle_b["input_hash"]


def test_missing_input_not_computable(tmp_path: Path) -> None:
    cycle, _, report = _run_artifacts(tmp_path, "RUN-GAP-MISSING-INPUT", required_input=None)
    assert cycle["status"] == "NOT_COMPUTABLE"
    assert report["status"] == "NOT_COMPUTABLE"
    assert report["promotion_decision"] == "HOLD"


def test_missing_artifact_fail(tmp_path: Path) -> None:
    run_id = "RUN-GAP-MISSING-ARTIFACT"
    cycle, index, _ = _run_artifacts(tmp_path, run_id, required_input={"input_state": "present", "source": "default"})
    run_dir = tmp_path / "artifacts_seal" / "runs" / run_id
    (run_dir / "live_run_projection.json").unlink()
    report = validate_gap_closure_artifacts(run_id=run_id, run_dir=run_dir, artifact_index=index["artifact_index"])
    assert cycle["status"] == "COMPLETE"
    assert report["status"] == "FAIL"
    assert report["promotion_decision"] == "HOLD"


def test_projection_boundary_enforced() -> None:
    cycle = build_gap_closure_cycle(
        run_id="RUN-GAP-FIRST-0001",
        mode="sandbox",
        workspace_only=True,
        required_input={"input_state": "present", "source": "default"},
    )
    projection = cycle["projection"]
    assert projection["authority_boundary"] == "projection cannot alter canon status"
    assert projection["projection_notice"] == "projection cannot alter canon status"


def test_oracle_bridge_correctness() -> None:
    cycle = build_gap_closure_cycle(
        run_id="RUN-GAP-FIRST-0001",
        mode="sandbox",
        workspace_only=True,
        required_input={"input_state": "present", "source": "default"},
    )
    bridge = cycle["bridge"]
    assert bridge["schema_version"] == "oracle_gap_bridge.v1"
    assert bridge["run_id"] == "RUN-GAP-FIRST-0001"
    assert bridge["gap_status"] == "COMPLETE"
    assert bridge["oracle_status"] == "DERIVED_ONLY"


def test_validation_output_correctness(tmp_path: Path) -> None:
    _, _, report = _run_artifacts(
        tmp_path,
        "RUN-GAP-VALID",
        required_input={"input_state": "present", "source": "default"},
    )
    assert report["status"] == "PASS"
    assert report["promotion_decision"] == "HOLD"
    assert "artifact_index_hash" in report
