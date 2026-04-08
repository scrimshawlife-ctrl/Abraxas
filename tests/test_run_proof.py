import json
import shutil
import subprocess
import sys
from pathlib import Path


def test_run_proof_generates_partial_summary():
    runtime_ledger = Path("out/runtime_artifact_ledger.jsonl")
    release_ledger = Path(".abraxas/ledger/release_manifests.jsonl")
    audit_ledger = Path(".abraxas/ledger/audit_reports.jsonl")

    runtime_before = runtime_ledger.read_text() if runtime_ledger.exists() else None
    release_before = release_ledger.read_text() if release_ledger.exists() else None
    audit_before = audit_ledger.read_text() if audit_ledger.exists() else None

    cp = subprocess.run(
        [sys.executable, "scripts/run_proof.py", "--subsystem", "oracle_signal_layer_v2"],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 0
    payload = json.loads(cp.stdout)
    assert payload["status"] in {"VALIDATOR-VISIBLE BUT PARTIAL", "CORRELATION-COMPLETE"}
    assert "testReceiptPath" in payload["artifacts"]
    assert "auditRecordPath" in payload["artifacts"]

    run_id = payload["runId"]
    run_dir = Path("out/proof_runs") / run_id
    if run_dir.exists():
        shutil.rmtree(run_dir)

    if runtime_before is None:
        if runtime_ledger.exists():
            runtime_ledger.unlink()
    else:
        runtime_ledger.write_text(runtime_before)

    if release_before is None:
        if release_ledger.exists():
            release_ledger.unlink()
    else:
        release_ledger.write_text(release_before)

    if audit_before is None:
        if audit_ledger.exists():
            audit_ledger.unlink()
    else:
        audit_ledger.write_text(audit_before)
