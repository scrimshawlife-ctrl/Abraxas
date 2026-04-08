#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from abx.proof_operator_summary_contracts import ProofOperatorSummary


REQUIRED_ARTIFACTS = [
    "runtime_artifact.json",
    "validator_artifact.json",
    "guardrail_receipts.json",
    "guardrail_validator_artifact.json",
    "test_receipt.json",
    "repo_status_receipt.json",
    "release_manifest_record.json",
    "audit_record.json",
    "attestation_summary.json",
]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _classify(attestation_status: str, missing_receipts: list[str], guardrail_status: str) -> str:
    if guardrail_status != "VALID":
        return "blocked"
    if attestation_status == "CORRELATION-COMPLETE" and not missing_receipts:
        return "candidate"
    if attestation_status == "VALIDATOR-VISIBLE BUT PARTIAL":
        return "partial"
    return "blocked"


def build_summary(run_dir: Path) -> ProofOperatorSummary:
    missing_files = [name for name in REQUIRED_ARTIFACTS if not (run_dir / name).exists()]
    if missing_files:
        return ProofOperatorSummary.build(
            status="NOT_COMPUTABLE",
            classification="blocked",
            run_dir=str(run_dir),
            missing_artifacts=missing_files,
        )

    attestation = _read_json(run_dir / "attestation_summary.json")
    guardrail_validator = _read_json(run_dir / "guardrail_validator_artifact.json")
    governance = _read_json(run_dir / "release_manifest_record.json")

    present_receipts = attestation.get("presentReceipts", [])
    missing_receipts = attestation.get("missingReceipts", [])
    attestation_status = str(attestation.get("status", ""))
    guardrail_status = str(guardrail_validator.get("status", ""))

    return ProofOperatorSummary.build(
        status="OK",
        classification=_classify(attestation_status, missing_receipts, guardrail_status),
        run_id=attestation.get("runId"),
        subsystem=attestation.get("subsystem"),
        attestation_status=attestation_status,
        guardrail_validator_status=guardrail_status,
        release_readiness=governance.get("release_readiness"),
        present_receipt_count=len(present_receipts),
        missing_receipt_count=len(missing_receipts),
        missing_receipts=missing_receipts,
        artifacts={
            name: str((run_dir / name).relative_to(ROOT))
            for name in REQUIRED_ARTIFACTS
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic operator summary for a proof run")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    run_dir = ROOT / "out" / "proof_runs" / args.run_id
    summary = build_summary(run_dir)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    print(f"PASS: wrote proof operator summary to {out_path}")
    return 0 if summary.status == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
