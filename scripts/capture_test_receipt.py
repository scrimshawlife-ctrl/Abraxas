#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture structured pytest receipt")
    parser.add_argument("--out", required=True)
    parser.add_argument(
        "--tests",
        nargs="*",
        default=[
            "tests/test_preflight.py",
            "tests/test_check_proof_claims.py",
            "tests/test_registry_consistency.py",
            "tests/test_release_readiness.py",
            "tests/test_governance_lint.py",
            "tests/test_append_governance_record.py",
            "tests/test_generate_release_manifest.py",
            "tests/test_governance_summary.py",
            "tests/test_validate_governance_record.py",
            "tests/test_reconcile_subsystem_state.py",
            "tests/test_continuity_drift_check.py",
            "tests/test_repo_status.py",
        ],
    )
    args = parser.parse_args()

    cmd = [sys.executable, "-m", "pytest", "-q", *args.tests]
    result = subprocess.run(cmd, capture_output=True, text=True)

    payload = {
        "timestamp": utc_now(),
        "label": "deterministic_test_pass",
        "command": cmd,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "status": "PASS" if result.returncode == 0 else "BLOCKED",
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    print(f"PASS: wrote test receipt to {out_path}")
    return 0 if result.returncode == 0 else result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
