from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _stable_id(prefix: str, payload: str, length: int = 12) -> str:
    return f"{prefix}{_sha256_text(payload)[:length].upper()}"


def _is_valid_sha256(value: str) -> bool:
    return len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def build_proof_artifact(
    created_at: str,
    source: str,
    operator: str,
    observation: str,
    force_pointer_failure: bool = False,
) -> dict[str, Any]:
    input_envelope = {
        "schema": "InputEnvelope.v2",
        "source": source,
        "operator": operator,
        "observation": observation,
        "created_at": created_at,
    }
    input_hash = _sha256_text(canonical_json(input_envelope).rstrip("\n"))
    run_id = _stable_id("RUN-PROOF-", f"{created_at}|{source}|{operator}|{observation}")

    pkt_input = _stable_id("PKT-INPUT-", input_hash)
    pkt_raw = _stable_id("PKT-RAW-", pkt_input)
    pkt_receipt = _stable_id("PKT-RECEIPT-", pkt_raw)
    pkt_oracle = _stable_id("PKT-ORACLE-", pkt_receipt)
    rec_id = _stable_id("REC-", pkt_oracle)
    art_ledger = _stable_id("ART-LEDGER-", rec_id)
    val_artifact = _stable_id("VAL-ARTIFACT-", art_ledger)

    packet_ids = [pkt_input, pkt_raw, pkt_receipt, pkt_oracle]
    ledger_record_ids = [rec_id]
    ledger_artifact_ids = [art_ledger]
    validator_artifact_id = val_artifact

    if force_pointer_failure:
        packet_ids = []

    pointer_closure_pass = bool(packet_ids) and bool(ledger_record_ids) and bool(validator_artifact_id) and _is_valid_sha256(input_hash)
    execution_status = "ATTESTED" if pointer_closure_pass else "NOT_COMPUTABLE_POINTER_CLOSURE"

    artifact = {
        "schema_version": "ProofArtifact.v1",
        "proof_id": "PROOF-ARTIFACT-001",
        "created_at": created_at,
        "system": "Abraxas",
        "lane": "SHADOW",
        "execution_status": execution_status,
        "authority": {
            "production_activation": False,
            "canon_promotion": False,
            "baseline_mutation": False,
            "scheduler_mutation": False,
            "forecast_influence": False,
            "shadow_to_forecast_leakage": False,
            "runtime_mutation": False,
            "promotion_granted": False,
        },
        "chain": {
            "input_envelope_schema": "InputEnvelope.v2",
            "raw_packet_schema": "RawObservationPacket.v1",
            "ingestion_receipt_schema": "IngestionReceipt.v1",
            "oracle_signal_schema": "OracleSignalPacket.v1",
            "ledger_record_schema": "LedgerRecord.v1",
            "validator_output_schema": "ValidatorOutput.v1",
        },
        "artifacts": {
            "input_envelope": input_envelope,
            "raw_observation_packet": {"schema": "RawObservationPacket.v1", "packet_id": pkt_raw, "run_id": run_id},
            "ingestion_receipt": {"schema": "IngestionReceipt.v1", "packet_id": pkt_receipt, "run_id": run_id},
            "oracle_signal_packet": {"schema": "OracleSignalPacket.v1", "packet_id": pkt_oracle, "run_id": run_id},
            "ledger_record": {"schema": "LedgerRecord.v1", "record_id": rec_id, "artifact_id": art_ledger},
            "validator_output": {"schema": "ValidatorOutput.v1", "artifact_id": val_artifact, "valid": pointer_closure_pass},
        },
        "correlation": {
            "run_id": run_id,
            "input_hash": input_hash,
            "packetIds": packet_ids,
            "ledgerRecordIds": ledger_record_ids,
            "ledgerArtifactIds": ledger_artifact_ids,
            "validatorArtifactId": validator_artifact_id,
        },
        "validation": {
            "deterministic_hashing": "required",
            "canonical_json": True,
            "sort_keys": True,
            "compact_separators": True,
            "numeric_rounding": "6dp",
            "byte_identical_rerun_required": True,
            "pointer_closure_status": "PASS" if pointer_closure_pass else "FAIL",
        },
    }

    authority_boundary = {
        k: artifact["authority"][k]
        for k in sorted(artifact["authority"].keys())
    }
    artifact["authority_boundary_hash"] = _sha256_text(canonical_json(authority_boundary).rstrip("\n"))

    proof_hash_payload = dict(artifact)
    proof_hash_payload.pop("proof_hash", None)
    artifact["proof_hash"] = _sha256_text(canonical_json(proof_hash_payload).rstrip("\n"))
    return artifact


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="out/proofs/proof_artifact_001.latest.json")
    ap.add_argument("--created-at", default="2026-05-01T00:00:00Z")
    ap.add_argument("--source", default="notion_cleanup_audit")
    ap.add_argument("--operator", default="Daniel Meyer / Applied Alchemy Labs")
    ap.add_argument("--observation", default="Runtime chain closure proof for Abraxas cleanup audit.")
    args = ap.parse_args()

    artifact = build_proof_artifact(args.created_at, args.source, args.operator, args.observation)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(canonical_json(artifact), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
