"""
Tests for DAP gap detection from ledgers.
"""

from pathlib import Path
import json

from abraxas.acquire.dap_builder import DapInputs, build_dap


def test_dap_gap_detection_from_ledgers(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ledgers_dir = tmp_path / "ledgers"
    ledgers_dir.mkdir()
    ledgers_dir.joinpath("forecast_scores.jsonl").write_text(
        (Path("tests/fixtures/dap/sample_ledgers/forecast_scores.jsonl").read_text())
    )
    ledgers_dir.joinpath("regime_scores.jsonl").write_text(
        (Path("tests/fixtures/dap/sample_ledgers/regime_scores.jsonl").read_text())
    )
    ledgers_dir.joinpath("component_scores.jsonl").write_text(
        (Path("tests/fixtures/dap/sample_ledgers/component_scores.jsonl").read_text())
    )

    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    inputs = DapInputs(
        forecast_scores_path=str(ledgers_dir / "forecast_scores.jsonl"),
        regime_scores_path=str(ledgers_dir / "regime_scores.jsonl"),
        component_scores_path=str(ledgers_dir / "component_scores.jsonl"),
    )

    json_path, _ = build_dap(
        run_id="dap_run",
        out_dir=str(reports_dir),
        playbook_path="tests/fixtures/acquire/playbook_sample.yaml",
        inputs=inputs,
        ts="2025-12-26T00:00:00Z",
    )

    plan = json.loads(Path(json_path).read_text())
    gap_kinds = [gap["kind"] for gap in plan["gaps"]]
    assert "COVERAGE_GAP" in gap_kinds
    assert "STRUCTURAL_GAP" in gap_kinds
