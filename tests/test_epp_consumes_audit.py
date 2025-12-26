from __future__ import annotations

import json
from pathlib import Path

from abraxas.evolve.epp_builder import build_epp


def test_epp_consumes_audit(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    audit_payload = {
        "run_id": "audit_run",
        "calibration": {
            "weeks": {"brier": 0.31, "n": 12},
            "months": {"brier": 0.15, "n": 30},
        },
    }
    audit_path = reports_dir / "forecast_audit_run123.json"
    audit_path.write_text(json.dumps(audit_payload), encoding="utf-8")

    ledger_path = tmp_path / "value_ledgers" / "epp_runs.jsonl"
    json_path, _ = build_epp(
        run_id="run123",
        out_dir=str(reports_dir),
        inputs_dir=str(reports_dir),
        osh_ledger_path=str(tmp_path / "osh.jsonl"),
        audit_path=str(audit_path),
        ledger_path=str(ledger_path),
        ts="2025-01-01T00:00:00Z",
    )

    report = json.loads(Path(json_path).read_text(encoding="utf-8"))
    kinds = {proposal["kind"] for proposal in report.get("proposals", [])}
    assert "CALIBRATION_POLICY_ADJUSTMENT" in kinds
