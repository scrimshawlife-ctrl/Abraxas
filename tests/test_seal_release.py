from __future__ import annotations

import json
from pathlib import Path

from scripts.seal_release import write_seal_report
from scripts.validate_artifacts import _load_schema, _validate_object


def test_write_seal_report_schema(tmp_path: Path):
    artifacts = {
        "trendpack": "trendpack.json",
        "trendpack_sha256": "a" * 64,
        "results_pack": "resultspack.json",
        "results_pack_sha256": "b" * 64,
        "runindex": "runindex.json",
        "runindex_sha256": "c" * 64,
        "viewpack": "viewpack.json",
        "viewpack_sha256": "d" * 64,
        "run_header": "runheader.json",
        "run_header_sha256": "e" * 64,
    }
    validation_result = {"ok": True, "validated_ticks": [0], "failures": []}
    dozen_gate_result = {
        "ok": True,
        "expected_trendpack_sha256": "f" * 64,
        "expected_runheader_sha256": "g" * 64,
        "first_mismatch_run": None,
        "divergence_kind": None,
    }

    report_path, report_sha = write_seal_report(
        artifacts_dir=str(tmp_path),
        run_id="seal",
        version="1.2.3",
        version_pack={"schema": "AbraxasVersionPack.v0", "abraxas": "1.2.3"},
        seal_tick_artifacts=artifacts,
        validation_result=validation_result,
        dozen_gate_result=dozen_gate_result,
    )

    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    schema = _load_schema("sealreport.v0", schemas_dir="schemas")
    errors = _validate_object(report, schema)

    assert errors == []
    assert report["ok"] is True
    assert len(report_sha) == 64
