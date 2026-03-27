from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

from abx.governance.types import WaiverAuditArtifact, WaiverRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable

WAIVERS_PATH = Path(__file__).resolve().parent / "frozen" / "waivers_v1.json"


def load_waiver_records() -> list[WaiverRecord]:
    if not WAIVERS_PATH.exists():
        return []
    payload = json.loads(WAIVERS_PATH.read_text(encoding="utf-8"))
    rows = []
    for entry in payload.get("waivers", []):
        rows.append(
            WaiverRecord(
                waiver_id=str(entry.get("waiver_id") or ""),
                owner=str(entry.get("owner") or ""),
                reason=str(entry.get("reason") or ""),
                scope=[str(x) for x in list(entry.get("scope") or [])],
                status=str(entry.get("status") or "REQUESTED"),
                expires_on=str(entry.get("expires_on") or ""),
                related_checks=[str(x) for x in list(entry.get("related_checks") or [])],
            )
        )
    return sorted(rows, key=lambda x: x.waiver_id)


def _classification(row: WaiverRecord) -> str:
    if not row.waiver_id or not row.owner or not row.scope or not row.expires_on:
        return "INVALID"
    if row.status not in {"APPROVED", "REJECTED", "REQUESTED"}:
        return "INVALID"
    if row.status != "APPROVED":
        return "INFORMATIONAL"
    if row.expires_on < str(date.today()):
        return "EXPIRED"
    return "ACTIVE"


def build_waiver_audit() -> WaiverAuditArtifact:
    rows = load_waiver_records()

    active: list[dict[str, Any]] = []
    expired: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []

    for row in rows:
        cls = _classification(row)
        payload = asdict(row) | {"classification": cls}
        if cls == "ACTIVE":
            active.append(payload)
        elif cls == "EXPIRED":
            expired.append(payload)
        elif cls == "INVALID":
            invalid.append(payload)

    result_payload = {
        "active": active,
        "expired": expired,
        "invalid": invalid,
    }
    audit_hash = sha256_bytes(dumps_stable(result_payload).encode("utf-8"))

    return WaiverAuditArtifact(
        artifact_type="WaiverAuditArtifact.v1",
        artifact_id="waiver-audit-abx",
        active_waivers=active,
        expired_waivers=expired,
        invalid_waivers=invalid,
        audit_hash=audit_hash,
    )
