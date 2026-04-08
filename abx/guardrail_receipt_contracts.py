from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

_ALLOWED_CHECK_STATUSES = {"PASS", "BLOCKED"}
_ALLOWED_BUNDLE_STATUSES = {"PASS", "PARTIAL"}


def _stable_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class GuardrailCheck:
    label: str
    timestamp: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    status: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GuardrailCheck":
        if payload.get("status") not in _ALLOWED_CHECK_STATUSES:
            raise ValueError(f"invalid check status: {payload.get('status')!r}")
        command = payload.get("command")
        if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
            raise ValueError("check command must be list[str]")
        return cls(
            label=str(payload.get("label", "")),
            timestamp=str(payload.get("timestamp", "")),
            command=command,
            returncode=int(payload.get("returncode", -1)),
            stdout=str(payload.get("stdout", "")),
            stderr=str(payload.get("stderr", "")),
            status=str(payload.get("status", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "timestamp": self.timestamp,
            "command": list(self.command),
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "status": self.status,
        }


@dataclass(frozen=True)
class GuardrailReceiptBundle:
    schema_version: int
    timestamp: str
    subsystem: str
    status: str
    receipts: list[str]
    checks: list[GuardrailCheck]
    receipt_bundle_id: str

    @classmethod
    def build(
        cls,
        timestamp: str,
        subsystem: str,
        status: str,
        receipts: list[str],
        checks: list[GuardrailCheck],
    ) -> "GuardrailReceiptBundle":
        if status not in _ALLOWED_BUNDLE_STATUSES:
            raise ValueError(f"invalid bundle status: {status!r}")
        deduped_receipts = sorted(set(receipts))
        fingerprint_payload = {
            "schema_version": 1,
            "timestamp": timestamp,
            "subsystem": subsystem,
            "status": status,
            "receipts": deduped_receipts,
            "checks": [item.to_dict() for item in checks],
        }
        receipt_bundle_id = hashlib.sha256(_stable_json(fingerprint_payload).encode("utf-8")).hexdigest()
        return cls(
            schema_version=1,
            timestamp=timestamp,
            subsystem=subsystem,
            status=status,
            receipts=deduped_receipts,
            checks=checks,
            receipt_bundle_id=receipt_bundle_id,
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GuardrailReceiptBundle":
        schema_version = int(payload.get("schema_version", 0))
        if schema_version != 1:
            raise ValueError(f"unsupported schema_version: {schema_version}")

        checks_payload = payload.get("checks")
        if not isinstance(checks_payload, list):
            raise ValueError("checks must be a list")
        checks = [GuardrailCheck.from_dict(item) for item in checks_payload]

        receipts = payload.get("receipts")
        if not isinstance(receipts, list) or not all(isinstance(item, str) for item in receipts):
            raise ValueError("receipts must be list[str]")

        bundle = cls.build(
            timestamp=str(payload.get("timestamp", "")),
            subsystem=str(payload.get("subsystem", "")),
            status=str(payload.get("status", "")),
            receipts=receipts,
            checks=checks,
        )

        provided_id = str(payload.get("receipt_bundle_id", ""))
        if bundle.receipt_bundle_id != provided_id:
            raise ValueError("receipt_bundle_id mismatch")
        return bundle

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "timestamp": self.timestamp,
            "subsystem": self.subsystem,
            "status": self.status,
            "receipts": list(self.receipts),
            "checks": [item.to_dict() for item in self.checks],
            "receipt_bundle_id": self.receipt_bundle_id,
        }
