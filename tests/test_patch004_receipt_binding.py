from pathlib import Path

from abx.repair.receipt_binding import (
    build_patch004_receipt_binding,
    validate_patch004_receipt_for_binding,
    write_patch004_binding_artifacts,
)


def _receipt(**kwargs):
    base = {
        "schema_version": "Patch004SandboxReceipt.v1",
        "run_id": "r-1",
        "manifest_id": "m-1",
        "actions_executed": 0,
        "files_modified": [],
        "execution_triggered": False,
        "runtime_mutation": False,
        "authority_leak_detected": False,
        "sandbox_only": True,
        "patch_004_execution_allowed": False,
    }
    base.update(kwargs)
    return base


def test_valid_binding_bound():
    binding = build_patch004_receipt_binding(_receipt(), manifest={"manifest_id": "m-1"})
    assert binding["binding_status"] == "BOUND"


def test_actions_executed_blocks():
    b = build_patch004_receipt_binding(_receipt(actions_executed=1))
    assert b["binding_status"] == "BLOCKED"


def test_files_modified_blocks():
    b = build_patch004_receipt_binding(_receipt(files_modified=["x.py"]))
    assert b["binding_status"] == "BLOCKED"


def test_execution_triggered_blocks():
    b = build_patch004_receipt_binding(_receipt(execution_triggered=True))
    assert b["binding_status"] == "BLOCKED"


def test_patch_execution_allowed_blocks():
    b = build_patch004_receipt_binding(_receipt(patch_004_execution_allowed=True))
    assert b["binding_status"] == "BLOCKED"


def test_hash_determinism(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    manifest = {"manifest_id": "m-1"}
    receipt = _receipt()
    a = write_patch004_binding_artifacts("run-1", manifest, receipt)
    b = write_patch004_binding_artifacts("run-1", manifest, receipt)
    assert a["manifest_sha256"] == b["manifest_sha256"]
    assert a["receipt_sha256"] == b["receipt_sha256"]


def test_sandbox_only_preserved():
    b = build_patch004_receipt_binding(_receipt(sandbox_only=True))
    assert b["sandbox_only"] is True


def test_validator_reasons():
    ok, reasons = validate_patch004_receipt_for_binding(_receipt(actions_executed=2))
    assert ok is False
    assert "actions_executed_nonzero" in reasons
