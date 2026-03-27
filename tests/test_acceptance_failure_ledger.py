from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from tools.acceptance.run_acceptance_suite import AcceptanceTestSuite


def test_emit_drift_report_writes_canonical_and_output_ledgers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    out_dir = tmp_path / "custom_acceptance_out"
    suite = AcceptanceTestSuite(
        input_path=tmp_path / "baseline.json",
        output_dir=out_dir,
        num_runs=3,
    )
    test_result = SimpleNamespace(
        test_id="A1_12_RUN_DETERMINISM",
        verdict="FAIL",
        details={
            "drift_classification": "ORDERING_INSTABILITY",
            "unique_hashes": ["a", "b"],
            "diff_paths": ["/claims/0"],
        },
    )

    suite._emit_drift_report(test_result, envelopes=[])

    canonical_path = tmp_path / "out" / "ledger" / "acceptance_failures.jsonl"
    local_path = out_dir / "acceptance_failures.jsonl"
    assert canonical_path.exists()
    assert local_path.exists()

    canonical_record = json.loads(canonical_path.read_text(encoding="utf-8").strip())
    local_record = json.loads(local_path.read_text(encoding="utf-8").strip())
    assert canonical_record == local_record
    assert canonical_record["metadata"]["ledger_paths"] == [
        "out/ledger/acceptance_failures.jsonl",
        local_path.as_posix(),
    ]
