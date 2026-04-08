import json
import shutil
import subprocess
import sys
from pathlib import Path


def test_validate_proof_operator_summary_pass_and_tamper(tmp_path: Path):
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
    summary_path = Path(payload["artifacts"]["proofOperatorSummaryPath"])
    out_valid = tmp_path / "summary_validator_valid.json"

    validate = subprocess.run(
        [
            sys.executable,
            "scripts/validate_proof_operator_summary.py",
            "--summary",
            str(summary_path),
            "--out",
            str(out_valid),
        ],
        capture_output=True,
        text=True,
    )
    assert validate.returncode == 0
    valid_payload = json.loads(out_valid.read_text())
    assert valid_payload["status"] == "VALID"

    tampered = json.loads(summary_path.read_text())
    tampered["classification"] = "blocked" if tampered["classification"] != "blocked" else "candidate"
    tampered_path = tmp_path / "tampered_summary.json"
    tampered_path.write_text(json.dumps(tampered, indent=2, sort_keys=True), encoding="utf-8")

    out_invalid = tmp_path / "summary_validator_invalid.json"
    invalid = subprocess.run(
        [
            sys.executable,
            "scripts/validate_proof_operator_summary.py",
            "--summary",
            str(tampered_path),
            "--out",
            str(out_invalid),
        ],
        capture_output=True,
        text=True,
    )
    assert invalid.returncode == 1
    invalid_payload = json.loads(out_invalid.read_text())
    assert invalid_payload["status"] == "INVALID"
    assert invalid_payload["errors"]

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
