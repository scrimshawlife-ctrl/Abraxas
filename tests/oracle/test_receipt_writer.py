from __future__ import annotations

from pathlib import Path

from abraxas.oracle.proof.receipt_writer import write_receipt_artifacts


def test_receipt_writer_emits_files(tmp_path: Path) -> None:
    out = {"run_id": "r1"}
    inv = {"status": "PASS"}
    val = {"hashes": {"input_hash": "a", "authority_hash": "b", "full_hash": "c"}}
    receipts = write_receipt_artifacts(output=out, invariance=inv, validator_summary=val, out_dir=str(tmp_path / "artifacts"))
    assert Path(receipts["runtime_artifact"]).exists()
    assert Path(receipts["invariance_artifact"]).exists()
    assert Path(receipts["validator_artifact"]).exists()
