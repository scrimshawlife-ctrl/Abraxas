#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from abx.mbom_v1_contracts import MBOMArtifact, MBOMRequest
from abraxas.oracle.mbom_v1 import assess_ambiguity

OUT_DIR = ROOT / "out" / "mbom_runs"
EXPECTED_SUBSYSTEMS_PATH = ROOT / ".abraxas" / "registries" / "expected_subsystems.yaml"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
    return result


def subsystem_is_registered(subsystem: str, expected_subsystems_path: Path) -> bool:
    expected = json.loads(expected_subsystems_path.read_text(encoding="utf-8"))
    return subsystem in expected.get("subsystems", [])


def build_not_computable(reason: str) -> dict:
    return {
        "timestamp": utc_now(),
        "subsystem": "mbom_v1",
        "status": "NOT_COMPUTABLE",
        "reason": reason,
        "artifacts": {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MBOM v1 deterministic model assessment")
    parser.add_argument("--request", required=True, help="Path to MBOM request JSON")
    parser.add_argument("--expected-subsystems", default=str(EXPECTED_SUBSYSTEMS_PATH))
    args = parser.parse_args()

    expected_subsystems_path = Path(args.expected_subsystems)

    try:
        registered = subsystem_is_registered("mbom_v1", expected_subsystems_path)
    except Exception:
        print(json.dumps(build_not_computable("expected_subsystems_unreadable_or_invalid"), indent=2, sort_keys=True))
        return 2

    if not registered:
        print(json.dumps(build_not_computable("subsystem_not_registered_in_expected_subsystems"), indent=2, sort_keys=True))
        return 2

    request = MBOMRequest.from_dict(json.loads(Path(args.request).read_text(encoding="utf-8")))

    run_dir = OUT_DIR / request.request_id
    run_dir.mkdir(parents=True, exist_ok=True)

    assessment = assess_ambiguity(
        lifecycle_states=request.lifecycle_states,
        domain_signals=request.domain_signals,
        resonance_score=request.resonance_score,
    ).to_dict()
    artifact = MBOMArtifact.build(request=request, assessment=assessment)

    artifact_path = run_dir / "mbom_assessment_artifact.json"
    artifact_path.write_text(json.dumps(artifact.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    artifact_sha256 = hashlib.sha256(artifact_path.read_bytes()).hexdigest()

    validator_path = run_dir / "mbom_assessment_validator.json"
    validate = run_cmd(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_mbom_v1_artifact.py"),
            "--artifact",
            str(artifact_path),
            "--out",
            str(validator_path),
        ]
    )
    if validate.returncode != 0:
        raise SystemExit(validate.returncode)

    governance_record = {
        "record_type": "audit_report",
        "timestamp": utc_now(),
        "subsystem": "mbom_v1",
        "summary": "MBOM model assessment artifact emitted.",
        "status": "SUCCESS",
        "provenance": {"source": "scripts/run_mbom_v1.py", "mode": "v1"},
        "correlation_pointers": [str(artifact_path.relative_to(ROOT))],
    }
    governance_record_path = run_dir / "mbom_audit_record.json"
    governance_record_path.write_text(json.dumps(governance_record, indent=2, sort_keys=True), encoding="utf-8")

    validate_governance = run_cmd(
        [
            sys.executable,
            str(ROOT / ".abraxas" / "scripts" / "validate_governance_record.py"),
            "--ledger",
            "audit_reports",
            "--record-file",
            str(governance_record_path),
        ]
    )
    if validate_governance.returncode != 0:
        raise SystemExit(validate_governance.returncode)

    append_governance = run_cmd(
        [
            sys.executable,
            str(ROOT / ".abraxas" / "scripts" / "append_governance_record.py"),
            "--ledger",
            "audit_reports",
            "--record-file",
            str(governance_record_path),
        ]
    )
    if append_governance.returncode != 0:
        raise SystemExit(append_governance.returncode)

    summary = {
        "timestamp": utc_now(),
        "subsystem": "mbom_v1",
        "lane": "support",
        "status": "MBOM_ASSESSMENT_EMITTED",
        "artifacts": {
            "mbomAssessmentArtifactPath": str(artifact_path.relative_to(ROOT)),
            "mbomAssessmentArtifactSha256": artifact_sha256,
            "assessmentId": artifact.assessment_id,
            "mbomAssessmentValidatorPath": str(validator_path.relative_to(ROOT)),
            "mbomAuditRecordPath": str(governance_record_path.relative_to(ROOT)),
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
