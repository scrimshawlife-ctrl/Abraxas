import json
import subprocess
import sys
from pathlib import Path


def test_run_mircl_v1_emits_artifacts_and_appends_audit(tmp_path: Path):
    request = tmp_path / "mircl_request.json"
    request.write_text(
        json.dumps(
            {
                "request_id": "MIRCL-REQ-0001",
                "prompt": "Map symbolic drift as advisory only",
                "context_tags": ["shadow", "mircl"],
            }
        ),
        encoding="utf-8",
    )

    audit_ledger = Path(".abraxas/ledger/audit_reports.jsonl")
    before = audit_ledger.read_text() if audit_ledger.exists() else None

    cp = subprocess.run(
        [sys.executable, "scripts/run_mircl_v1.py", "--request", str(request)],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 0

    payload = json.loads(cp.stdout)
    assert payload["subsystem"] == "mircl_v1"
    assert payload["lane"] == "shadow"
    assert payload["status"] == "SHADOW_ADVISORY_EMITTED"

    artifact = Path(payload["artifacts"]["mirclAdvisoryArtifactPath"])
    validator = Path(payload["artifacts"]["mirclAdvisoryValidatorPath"])
    audit_record = Path(payload["artifacts"]["mirclAuditRecordPath"])

    assert artifact.exists()
    assert validator.exists()
    assert audit_record.exists()

    validator_payload = json.loads(validator.read_text())
    assert validator_payload["status"] == "VALID"

    if before is None:
        if audit_ledger.exists():
            audit_ledger.unlink()
    else:
        audit_ledger.write_text(before)
