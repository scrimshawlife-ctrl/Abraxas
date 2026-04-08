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

from abx.guardrail_receipt_contracts import GuardrailCheck, GuardrailReceiptBundle


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_command(label: str, cmd: list[str]) -> GuardrailCheck:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return GuardrailCheck(
        label=label,
        timestamp=utc_now(),
        command=cmd,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        status="PASS" if result.returncode == 0 else "BLOCKED",
    )


def build_receipt_bundle(subsystem: str) -> GuardrailReceiptBundle:
    checks = [
        run_command(
            "registry_consistency",
            [sys.executable, str(ROOT / ".abraxas" / "scripts" / "registry_consistency.py")],
        ),
        run_command(
            "governance_lint",
            [sys.executable, str(ROOT / ".abraxas" / "scripts" / "governance_lint.py")],
        ),
        run_command(
            "release_readiness",
            [
                sys.executable,
                str(ROOT / ".abraxas" / "scripts" / "release_readiness.py"),
                "--subsystem",
                subsystem,
                "--receipts",
                "runtime_artifact",
                "validator_artifact",
            ],
        ),
        run_command(
            "reconcile_subsystem",
            [
                sys.executable,
                str(ROOT / ".abraxas" / "scripts" / "reconcile_subsystem_state.py"),
                "--ledger",
                str(ROOT / ".abraxas" / "ledger" / "release_manifests.jsonl"),
            ],
        ),
    ]

    receipt_names: list[str] = []
    for item in checks:
        if item.label == "registry_consistency" and item.returncode == 0:
            receipt_names.append("registry_consistency_pass")
        if item.label == "governance_lint" and item.returncode == 0:
            receipt_names.append("governance_lint_pass")
        if item.label == "release_readiness" and item.returncode == 0:
            receipt_names.append("release_readiness_pass")
        if item.label == "reconcile_subsystem" and item.returncode == 0:
            receipt_names.append("reconciliation_pass")

    overall_status = "PASS" if all(item.returncode == 0 for item in checks) else "PARTIAL"

    return GuardrailReceiptBundle.build(
        timestamp=utc_now(),
        subsystem=subsystem,
        status=overall_status,
        receipts=receipt_names,
        checks=checks,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture structured guardrail receipts for a subsystem")
    parser.add_argument("--subsystem", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    bundle = build_receipt_bundle(args.subsystem)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(bundle.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    print(f"PASS: wrote receipt bundle to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
