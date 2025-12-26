"""
Tests for DAP action selection ordering.
"""

from pathlib import Path
import json

from abraxas.acquire.dap_builder import DapInputs, build_dap


def test_dap_action_selection_online_vs_offline(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    ledgers_dir = tmp_path / "ledgers"
    ledgers_dir.mkdir()
    ledgers_dir.joinpath("regime_scores.jsonl").write_text(
        Path("tests/fixtures/dap/sample_ledgers/regime_scores.jsonl").read_text()
    )

    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    smv_report = {
        "units": [{"unit_id": "ai_deepfake_policy", "smv_overall": 0.2}]
    }
    (reports_dir / "smv_run.json").write_text(json.dumps(smv_report))

    inputs = DapInputs(
        regime_scores_path=str(ledgers_dir / "regime_scores.jsonl"),
        smv_report_path=str(reports_dir / "smv_run.json"),
    )

    json_path, _ = build_dap(
        run_id="dap_run",
        out_dir=str(reports_dir),
        playbook_path="tests/fixtures/acquire/playbook_sample.yaml",
        inputs=inputs,
        ts="2025-12-26T00:00:00Z",
    )

    plan = json.loads(Path(json_path).read_text())
    assert plan["actions"]
    assert plan["actions"][0]["kind"] == "ONLINE_FETCH"
