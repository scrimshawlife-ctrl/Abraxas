import json
import shutil
import subprocess
import sys
from pathlib import Path


def test_summarize_proof_run_emits_candidate_or_partial(tmp_path: Path):
    runtime_ledger = Path("out/runtime_artifact_ledger.jsonl")
    release_ledger = Path(".abraxas/ledger/release_manifests.jsonl")
    audit_ledger = Path(".abraxas/ledger/audit_reports.jsonl")

    runtime_before = runtime_ledger.read_text() if runtime_ledger.exists() else None
    release_before = release_ledger.read_text() if release_ledger.exists() else None
    audit_before = audit_ledger.read_text() if audit_ledger.exists() else None

    proof = subprocess.run(
        [sys.executable, "scripts/run_proof.py", "--subsystem", "oracle_signal_layer_v2"],
        capture_output=True,
        text=True,
    )
    assert proof.returncode == 0
    payload = json.loads(proof.stdout)
    run_id = payload["runId"]

    out = tmp_path / "summary.json"
    summary_cp = subprocess.run(
        [
            sys.executable,
            "scripts/summarize_proof_run.py",
            "--run-id",
            run_id,
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    assert summary_cp.returncode == 0
    summary = json.loads(out.read_text())
    assert summary["status"] == "OK"
    assert summary["classification"] in {"candidate", "partial"}
    assert summary["schema_version"] == 1
    assert summary["summary_id"]

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
