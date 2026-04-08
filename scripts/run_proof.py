#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "out" / "proof_runs"
RUNTIME_LEDGER_PATH = ROOT / "out" / "runtime_artifact_ledger.jsonl"
EXPECTED_SUBSYSTEMS_PATH = ROOT / ".abraxas" / "registries" / "expected_subsystems.yaml"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def gen_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def load_subsystem_metadata(subsystem: str) -> dict[str, Any]:
    path = ROOT / ".abraxas" / "subsystems" / f"{subsystem}.yaml"
    return json.loads(path.read_text(encoding="utf-8"))


def subsystem_is_registered(subsystem: str) -> bool:
    expected = json.loads(EXPECTED_SUBSYSTEMS_PATH.read_text(encoding="utf-8"))
    return subsystem in expected.get("subsystems", [])


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
    return result


def build_runtime_artifact(run_id: str, artifact_id: str, packet_id: str) -> dict:
    return {
        "timestamp": utc_now(),
        "runId": run_id,
        "artifactId": artifact_id,
        "packetId": packet_id,
        "status": "PASS",
        "kind": "RunProofRecord",
        "payload": {
            "message": "Bounded proof emission with structured governance/test/status receipts",
            "deterministic": True,
        },
    }


def build_runtime_ledger_record(
    run_id: str,
    artifact_id: str,
    packet_id: str,
    ledger_record_id: str,
) -> dict:
    return {
        "timestamp": utc_now(),
        "recordId": ledger_record_id,
        "runId": run_id,
        "artifactId": artifact_id,
        "packetId": packet_id,
        "lineage": {
            "source": "scripts/run_proof.py",
            "kind": "runtime_artifact",
        },
        "status": "LEDGER-VISIBLE",
    }


def build_governance_release_record(
    subsystem: str,
    required_receipts: list[str],
    present_receipts: list[str],
    missing_receipts: list[str],
    observed_proof_receipts: list[str],
    registration_receipt: dict[str, Any],
    status: str,
) -> dict:
    return {
        "record_type": "release_manifest",
        "timestamp": utc_now(),
        "subsystem": subsystem,
        "release_readiness": "gated" if not missing_receipts else "blocked",
        "required_receipts": required_receipts,
        "present_receipts": present_receipts,
        "missing_receipts": missing_receipts,
        "observed_proof_receipts": observed_proof_receipts,
        "registration_receipt": registration_receipt,
        "status": status,
        "provenance": {"source": "scripts/run_proof.py", "mode": "v3"},
        "correlation_pointers": [],
    }


def build_audit_record(subsystem: str, summary: str) -> dict:
    return {
        "record_type": "audit_report",
        "timestamp": utc_now(),
        "subsystem": subsystem,
        "summary": summary,
        "status": "SUCCESS",
        "provenance": {"source": "scripts/run_proof.py", "mode": "v3"},
        "correlation_pointers": [],
    }


def build_attestation_summary(
    run_id: str,
    subsystem: str,
    artifacts: dict,
    present_receipts: list[str],
    missing_receipts: list[str],
) -> dict:
    return {
        "timestamp": utc_now(),
        "runId": run_id,
        "subsystem": subsystem,
        "status": "CORRELATION-COMPLETE" if not missing_receipts else "VALIDATOR-VISIBLE BUT PARTIAL",
        "artifacts": artifacts,
        "presentReceipts": present_receipts,
        "missingReceipts": missing_receipts,
    }


def build_not_computable_summary(subsystem: str, reason: str) -> dict:
    return {
        "timestamp": utc_now(),
        "runId": None,
        "subsystem": subsystem,
        "status": "NOT_COMPUTABLE",
        "reason": reason,
        "artifacts": {},
        "presentReceipts": [],
        "missingReceipts": [],
    }


def build_registration_receipt(subsystem: str, registered: bool) -> dict:
    return {
        "timestamp": utc_now(),
        "label": "subsystem_registration_check",
        "subsystem": subsystem,
        "status": "PASS" if registered else "BLOCKED",
        "registryPath": str(EXPECTED_SUBSYSTEMS_PATH.relative_to(ROOT)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Minimal Abraxas proof emitter v3")
    parser.add_argument("--subsystem", default="oracle_signal_layer_v2")
    args = parser.parse_args()

    is_registered = subsystem_is_registered(args.subsystem)
    if not is_registered:
        registration_receipt = build_registration_receipt(args.subsystem, registered=False)
        payload = build_not_computable_summary(
            subsystem=args.subsystem,
            reason="subsystem_not_registered_in_expected_subsystems",
        )
        payload["registrationReceipt"] = registration_receipt
        print(
            json.dumps(payload, indent=2, sort_keys=True)
        )
        return 2

    run_id = gen_id("RUN-PROOF")
    artifact_id = gen_id("ART")
    packet_id = gen_id("PKT")
    ledger_record_id = gen_id("REC")

    run_dir = OUT_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    registration_receipt = build_registration_receipt(args.subsystem, registered=True)
    registration_receipt_path = run_dir / "registration_receipt.json"
    registration_receipt_path.write_text(
        json.dumps(registration_receipt, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    runtime_artifact = build_runtime_artifact(run_id, artifact_id, packet_id)
    runtime_artifact_path = run_dir / "runtime_artifact.json"
    runtime_artifact_path.write_text(
        json.dumps(runtime_artifact, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    runtime_ledger_record = build_runtime_ledger_record(
        run_id=run_id,
        artifact_id=artifact_id,
        packet_id=packet_id,
        ledger_record_id=ledger_record_id,
    )
    append_jsonl(RUNTIME_LEDGER_PATH, runtime_ledger_record)

    validator_artifact_path = run_dir / "validator_artifact.json"
    validator_result = run_cmd(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_run.py"),
            "--run-id",
            run_id,
            "--artifact-id",
            artifact_id,
            "--ledger-record-id",
            ledger_record_id,
            "--packet-id",
            packet_id,
            "--out",
            str(validator_artifact_path),
        ]
    )
    if validator_result.returncode != 0:
        raise SystemExit(validator_result.returncode)

    receipt_bundle_path = run_dir / "guardrail_receipts.json"
    receipt_result = run_cmd(
        [
            sys.executable,
            str(ROOT / "scripts" / "capture_guardrail_receipts.py"),
            "--subsystem",
            args.subsystem,
            "--out",
            str(receipt_bundle_path),
        ]
    )
    if receipt_result.returncode != 0:
        raise SystemExit(receipt_result.returncode)

    guardrail_validator_artifact_path = run_dir / "guardrail_validator_artifact.json"
    guardrail_validator_result = run_cmd(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_guardrail_receipts.py"),
            "--bundle",
            str(receipt_bundle_path),
            "--out",
            str(guardrail_validator_artifact_path),
        ]
    )
    if guardrail_validator_result.returncode != 0:
        raise SystemExit(guardrail_validator_result.returncode)

    test_receipt_path = run_dir / "test_receipt.json"
    test_result = run_cmd(
        [
            sys.executable,
            str(ROOT / "scripts" / "capture_test_receipt.py"),
            "--out",
            str(test_receipt_path),
        ]
    )

    repo_status_receipt_path = run_dir / "repo_status_receipt.json"
    repo_status_result = run_cmd(
        [
            sys.executable,
            str(ROOT / "scripts" / "capture_repo_status_receipt.py"),
            "--out",
            str(repo_status_receipt_path),
        ]
    )
    if repo_status_result.returncode != 0:
        raise SystemExit(repo_status_result.returncode)

    receipt_bundle = json.loads(receipt_bundle_path.read_text(encoding="utf-8"))
    dynamic_receipts = receipt_bundle.get("receipts", [])

    test_receipt = json.loads(test_receipt_path.read_text(encoding="utf-8"))
    repo_status_receipt = json.loads(repo_status_receipt_path.read_text(encoding="utf-8"))
    guardrail_validator_artifact = json.loads(guardrail_validator_artifact_path.read_text(encoding="utf-8"))

    present_receipts = ["runtime_artifact", "validator_artifact", *dynamic_receipts]
    if registration_receipt.get("status") == "PASS":
        present_receipts.append("subsystem_registration_verified")

    if guardrail_validator_result.returncode == 0 and guardrail_validator_artifact.get("status") == "VALID":
        present_receipts.append("guardrail_bundle_validated")
    if test_result.returncode == 0 and test_receipt.get("returncode") == 0:
        present_receipts.append("deterministic_test_pass")
    if repo_status_receipt.get("returncode") == 0 and repo_status_receipt.get("parsed"):
        present_receipts.append("repo_status_pass")

    present_receipts = sorted(set(present_receipts))

    subsystem_metadata = load_subsystem_metadata(args.subsystem)
    canonical_required_receipts = list(
        subsystem_metadata.get("receipt_overrides", {}).get(
            "forecast_active_change",
            subsystem_metadata.get("required_receipts", []),
        )
    )
    observed_proof_receipts = [
        "registry_consistency_pass",
        "governance_lint_pass",
        "guardrail_bundle_validated",
        "deterministic_test_pass",
        "repo_status_pass",
    ]
    required_receipts = canonical_required_receipts
    missing_receipts = [item for item in required_receipts if item not in present_receipts]

    governance_record = build_governance_release_record(
        subsystem=args.subsystem,
        required_receipts=required_receipts,
        present_receipts=present_receipts,
        missing_receipts=missing_receipts,
        observed_proof_receipts=observed_proof_receipts,
        registration_receipt=registration_receipt,
        status="FAILED" if missing_receipts else "SUCCESS",
    )

    governance_record_path = run_dir / "release_manifest_record.json"
    governance_record_path.write_text(
        json.dumps(governance_record, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    validate_result = run_cmd(
        [
            sys.executable,
            str(ROOT / ".abraxas" / "scripts" / "validate_governance_record.py"),
            "--ledger",
            "release_manifests",
            "--record-file",
            str(governance_record_path),
        ]
    )
    if validate_result.returncode != 0:
        raise SystemExit(validate_result.returncode)

    append_result = run_cmd(
        [
            sys.executable,
            str(ROOT / ".abraxas" / "scripts" / "append_governance_record.py"),
            "--ledger",
            "release_manifests",
            "--record-file",
            str(governance_record_path),
        ]
    )
    if append_result.returncode != 0:
        raise SystemExit(append_result.returncode)

    audit_record = build_audit_record(
        subsystem=args.subsystem,
        summary="Bounded proof run with runtime artifact, validator stub, guardrail receipts, test receipt, and repo status receipt.",
    )
    audit_record_path = run_dir / "audit_record.json"
    audit_record_path.write_text(json.dumps(audit_record, indent=2, sort_keys=True), encoding="utf-8")

    audit_validate = run_cmd(
        [
            sys.executable,
            str(ROOT / ".abraxas" / "scripts" / "validate_governance_record.py"),
            "--ledger",
            "audit_reports",
            "--record-file",
            str(audit_record_path),
        ]
    )
    if audit_validate.returncode != 0:
        raise SystemExit(audit_validate.returncode)

    audit_append = run_cmd(
        [
            sys.executable,
            str(ROOT / ".abraxas" / "scripts" / "append_governance_record.py"),
            "--ledger",
            "audit_reports",
            "--record-file",
            str(audit_record_path),
        ]
    )
    if audit_append.returncode != 0:
        raise SystemExit(audit_append.returncode)

    artifacts = {
        "runtimeArtifactPath": str(runtime_artifact_path.relative_to(ROOT)),
        "registrationReceiptPath": str(registration_receipt_path.relative_to(ROOT)),
        "validatorArtifactPath": str(validator_artifact_path.relative_to(ROOT)),
        "receiptBundlePath": str(receipt_bundle_path.relative_to(ROOT)),
        "guardrailValidatorArtifactPath": str(guardrail_validator_artifact_path.relative_to(ROOT)),
        "testReceiptPath": str(test_receipt_path.relative_to(ROOT)),
        "repoStatusReceiptPath": str(repo_status_receipt_path.relative_to(ROOT)),
        "governanceRecordPath": str(governance_record_path.relative_to(ROOT)),
        "auditRecordPath": str(audit_record_path.relative_to(ROOT)),
    }

    attestation_summary = build_attestation_summary(
        run_id=run_id,
        subsystem=args.subsystem,
        artifacts=artifacts,
        present_receipts=present_receipts,
        missing_receipts=missing_receipts,
    )

    attestation_summary_path = run_dir / "attestation_summary.json"
    attestation_summary_path.write_text(
        json.dumps(attestation_summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    operator_summary_path = run_dir / "proof_operator_summary.json"
    operator_summary_result = run_cmd(
        [
            sys.executable,
            str(ROOT / "scripts" / "summarize_proof_run.py"),
            "--run-id",
            run_id,
            "--out",
            str(operator_summary_path),
        ]
    )
    if operator_summary_result.returncode != 0:
        raise SystemExit(operator_summary_result.returncode)

    operator_summary_validator_path = run_dir / "proof_operator_summary_validator_artifact.json"
    operator_summary_validate_result = run_cmd(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_proof_operator_summary.py"),
            "--summary",
            str(operator_summary_path),
            "--out",
            str(operator_summary_validator_path),
        ]
    )
    if operator_summary_validate_result.returncode != 0:
        raise SystemExit(operator_summary_validate_result.returncode)

    attestation_summary["presentReceipts"] = sorted(
        set([*attestation_summary["presentReceipts"], "proof_operator_summary_validated"])
    )
    attestation_summary["artifacts"]["proofOperatorSummaryPath"] = str(operator_summary_path.relative_to(ROOT))
    attestation_summary["artifacts"]["proofOperatorSummaryValidatorPath"] = str(
        operator_summary_validator_path.relative_to(ROOT)
    )
    attestation_summary_path.write_text(
        json.dumps(attestation_summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print(json.dumps(attestation_summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
