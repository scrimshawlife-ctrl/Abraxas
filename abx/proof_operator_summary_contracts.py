from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

_ALLOWED_STATUS = {"OK", "NOT_COMPUTABLE"}
_ALLOWED_CLASSIFICATIONS = {"candidate", "partial", "blocked"}


def _stable_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class ProofOperatorSummary:
    schema_version: int
    status: str
    classification: str
    run_id: str | None
    subsystem: str | None
    attestation_status: str | None
    guardrail_validator_status: str | None
    release_readiness: str | None
    present_receipt_count: int | None
    missing_receipt_count: int | None
    missing_receipts: list[str] | None
    artifacts: dict[str, str] | None
    run_dir: str | None
    missing_artifacts: list[str] | None
    summary_id: str

    @classmethod
    def build(
        cls,
        *,
        status: str,
        classification: str,
        run_id: str | None = None,
        subsystem: str | None = None,
        attestation_status: str | None = None,
        guardrail_validator_status: str | None = None,
        release_readiness: str | None = None,
        present_receipt_count: int | None = None,
        missing_receipt_count: int | None = None,
        missing_receipts: list[str] | None = None,
        artifacts: dict[str, str] | None = None,
        run_dir: str | None = None,
        missing_artifacts: list[str] | None = None,
    ) -> "ProofOperatorSummary":
        if status not in _ALLOWED_STATUS:
            raise ValueError(f"invalid status: {status!r}")
        if classification not in _ALLOWED_CLASSIFICATIONS:
            raise ValueError(f"invalid classification: {classification!r}")

        payload = {
            "schema_version": 1,
            "status": status,
            "classification": classification,
            "runId": run_id,
            "subsystem": subsystem,
            "attestationStatus": attestation_status,
            "guardrailValidatorStatus": guardrail_validator_status,
            "releaseReadiness": release_readiness,
            "presentReceiptCount": present_receipt_count,
            "missingReceiptCount": missing_receipt_count,
            "missingReceipts": missing_receipts,
            "artifacts": artifacts,
            "runDir": run_dir,
            "missingArtifacts": missing_artifacts,
        }
        summary_id = hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()
        return cls(
            schema_version=1,
            status=status,
            classification=classification,
            run_id=run_id,
            subsystem=subsystem,
            attestation_status=attestation_status,
            guardrail_validator_status=guardrail_validator_status,
            release_readiness=release_readiness,
            present_receipt_count=present_receipt_count,
            missing_receipt_count=missing_receipt_count,
            missing_receipts=missing_receipts,
            artifacts=artifacts,
            run_dir=run_dir,
            missing_artifacts=missing_artifacts,
            summary_id=summary_id,
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ProofOperatorSummary":
        if int(payload.get("schema_version", 0)) != 1:
            raise ValueError("unsupported schema_version")

        if "missingArtifacts" in payload:
            built = cls.build(
                status=str(payload.get("status", "")),
                classification=str(payload.get("classification", "")),
                run_dir=str(payload.get("runDir", "")),
                missing_artifacts=list(payload.get("missingArtifacts", [])),
            )
        else:
            built = cls.build(
                status=str(payload.get("status", "")),
                classification=str(payload.get("classification", "")),
                run_id=str(payload.get("runId", "")),
                subsystem=str(payload.get("subsystem", "")),
                attestation_status=str(payload.get("attestationStatus", "")),
                guardrail_validator_status=str(payload.get("guardrailValidatorStatus", "")),
                release_readiness=str(payload.get("releaseReadiness", "")),
                present_receipt_count=int(payload.get("presentReceiptCount", 0)),
                missing_receipt_count=int(payload.get("missingReceiptCount", 0)),
                missing_receipts=list(payload.get("missingReceipts", [])),
                artifacts=dict(payload.get("artifacts", {})),
            )

        if built.summary_id != str(payload.get("summary_id", "")):
            raise ValueError("summary_id mismatch")
        return built

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "schema_version": self.schema_version,
            "status": self.status,
            "classification": self.classification,
            "summary_id": self.summary_id,
        }
        if self.status == "NOT_COMPUTABLE":
            data["runDir"] = self.run_dir
            data["missingArtifacts"] = self.missing_artifacts or []
        else:
            data.update(
                {
                    "runId": self.run_id,
                    "subsystem": self.subsystem,
                    "attestationStatus": self.attestation_status,
                    "guardrailValidatorStatus": self.guardrail_validator_status,
                    "releaseReadiness": self.release_readiness,
                    "presentReceiptCount": self.present_receipt_count,
                    "missingReceiptCount": self.missing_receipt_count,
                    "missingReceipts": self.missing_receipts or [],
                    "artifacts": self.artifacts or {},
                }
            )
        return data
