#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from abx.mircl_v1_contracts import MirclAdvisoryArtifact, MirclRequest

OUT_DIR = ROOT / "out" / "mircl_runs"
EXPECTED_SUBSYSTEMS_PATH = ROOT / ".abraxas" / "registries" / "expected_subsystems.yaml"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
    return result


def subsystem_is_registered(subsystem: str) -> bool:
    expected = json.loads(EXPECTED_SUBSYSTEMS_PATH.read_text(encoding="utf-8"))
    return subsystem in expected.get("subsystems", [])


def build_not_computable(reason: str) -> dict:
    return {
        "timestamp": utc_now(),
        "subsystem": "mircl_v1",
        "status": "NOT_COMPUTABLE",
        "reason": reason,
        "artifacts": {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MIRCL v1 shadow advisory execution")
    parser.add_argument("--request", required=True, help="Path to request JSON")
    args = parser.parse_args()

    if not subsystem_is_registered("mircl_v1"):
        print(json.dumps(build_not_computable("subsystem_not_registered_in_expected_subsystems"), indent=2, sort_keys=True))
        return 2

    request_payload = json.loads(Path(args.request).read_text(encoding="utf-8"))
    request = MirclRequest.from_dict(request_payload)

    run_dir = OUT_DIR / request.request_id
    run_dir.mkdir(parents=True, exist_ok=True)

    artifact = MirclAdvisoryArtifact.build(request)
    artifact_path = run_dir / "mircl_advisory_artifact.json"
    artifact_path.write_text(json.dumps(artifact.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    validator_path = run_dir / "mircl_advisory_validator.json"
    validate = run_cmd(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_mircl_v1_artifact.py"),
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
        "subsystem": "mircl_v1",
        "summary": "MIRCL shadow advisory artifact emitted.",
        "status": "SUCCESS",
        "provenance": {"source": "scripts/run_mircl_v1.py", "mode": "v1"},
        "correlation_pointers": [str(artifact_path.relative_to(ROOT))],
    }
    governance_record_path = run_dir / "mircl_audit_record.json"
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
        "subsystem": "mircl_v1",
        "lane": "shadow",
        "status": "SHADOW_ADVISORY_EMITTED",
        "artifacts": {
            "mirclAdvisoryArtifactPath": str(artifact_path.relative_to(ROOT)),
            "mirclAdvisoryValidatorPath": str(validator_path.relative_to(ROOT)),
            "mirclAuditRecordPath": str(governance_record_path.relative_to(ROOT)),
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
