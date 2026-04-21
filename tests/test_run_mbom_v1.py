import json
import subprocess
import sys
import hashlib
from pathlib import Path


def test_run_mbom_v1_emits_artifacts_and_appends_audit(tmp_path: Path):
    request = tmp_path / "mbom_request.json"
    request.write_text(
        json.dumps(
            {
                "request_id": "MBOM-REQ-0001",
                "lifecycle_states": {"a": "SEED", "b": "STABLE"},
                "domain_signals": ["sig-a", "sig-b"],
                "resonance_score": 0.4,
            }
        ),
        encoding="utf-8",
    )

    audit_ledger = Path(".abraxas/ledger/audit_reports.jsonl")
    before = audit_ledger.read_text() if audit_ledger.exists() else None

    cp = subprocess.run(
        [sys.executable, "scripts/run_mbom_v1.py", "--request", str(request)],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 0

    payload = json.loads(cp.stdout)
    assert payload["subsystem"] == "mbom_v1"
    assert payload["lane"] == "support"
    assert payload["status"] == "MBOM_ASSESSMENT_EMITTED"

    artifact = Path(payload["artifacts"]["mbomAssessmentArtifactPath"])
    validator = Path(payload["artifacts"]["mbomAssessmentValidatorPath"])
    audit_record = Path(payload["artifacts"]["mbomAuditRecordPath"])

    assert artifact.exists()
    assert validator.exists()
    assert audit_record.exists()
    assert payload["artifacts"]["assessmentId"]
    assert payload["artifacts"]["mbomAssessmentArtifactSha256"] == hashlib.sha256(artifact.read_bytes()).hexdigest()

    validator_payload = json.loads(validator.read_text())
    assert validator_payload["status"] == "VALID"
    audit_payload = json.loads(audit_record.read_text())
    assert artifact.as_posix() in audit_payload["correlation_pointers"]
    assert validator.as_posix() in audit_payload["correlation_pointers"]
    assert audit_payload["correlation_pointer_state"] == "present"
    assert audit_payload["correlation_pointer_unresolved_reasons"] == []

    if before is None:
        if audit_ledger.exists():
            audit_ledger.unlink()
    else:
        audit_ledger.write_text(before)
