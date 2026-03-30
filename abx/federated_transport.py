from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class RemoteEvidenceStatus(str, Enum):
    NOT_DECLARED = "NOT_DECLARED"
    MISSING = "MISSING"
    MALFORMED = "MALFORMED"
    VALID = "VALID"
    PARTIAL = "PARTIAL"
    INCONSISTENT = "INCONSISTENT"
    STALE = "STALE"


@dataclass(frozen=True)
class RemoteEvidenceResult:
    status: RemoteEvidenceStatus
    manifest_path: str
    manifest_id: str = ""
    manifest_schema: str = ""
    origin: str = ""
    run_id: str = ""
    packet_ids: list[str] = field(default_factory=list)
    packet_count: int = 0
    valid_packet_count: int = 0
    invalid_packet_count: int = 0
    stale_packet_count: int = 0
    inconsistent: bool = False
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _parse_timestamp(value: str) -> datetime | None:
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def verify_remote_evidence_manifest(
    manifest_ref: str | None,
    *,
    base_dir: Path = Path("."),
    now: datetime | None = None,
    max_age_days: int = 14,
) -> RemoteEvidenceResult:
    if not manifest_ref:
        return RemoteEvidenceResult(status=RemoteEvidenceStatus.NOT_DECLARED, manifest_path="")

    manifest_path = (base_dir / manifest_ref).resolve() if not Path(manifest_ref).is_absolute() else Path(manifest_ref)
    if not manifest_path.exists():
        return RemoteEvidenceResult(
            status=RemoteEvidenceStatus.MISSING,
            manifest_path=manifest_path.as_posix(),
            errors=["remote_evidence_manifest_missing"],
        )

    payload = _load_json(manifest_path)
    if payload is None:
        return RemoteEvidenceResult(
            status=RemoteEvidenceStatus.MALFORMED,
            manifest_path=manifest_path.as_posix(),
            errors=["remote_evidence_manifest_unreadable"],
        )

    errors: list[str] = []
    manifest_schema = str(payload.get("schema", "")).strip()
    if manifest_schema not in {"RemoteEvidenceManifest.v0", "RemoteEvidenceManifest.v1"}:
        errors.append("remote_evidence_manifest_schema_invalid")

    manifest_id = str(payload.get("manifest_id", "")).strip()
    if not manifest_id:
        errors.append("remote_evidence_manifest_id_missing")

    origin = str(payload.get("origin", "")).strip().lower()
    if not origin:
        errors.append("remote_evidence_origin_missing")

    manifest_run_id = str(payload.get("run_id", "")).strip()
    if manifest_schema == "RemoteEvidenceManifest.v1" and not manifest_run_id:
        errors.append("remote_evidence_manifest_run_id_missing")

    packets_raw = payload.get("packets", [])
    packets = packets_raw if isinstance(packets_raw, list) else []
    if not packets:
        errors.append("remote_evidence_packets_missing")

    valid_statuses = {"VALID", "PASS", "SUCCESS"}
    invalid_statuses = {"FAIL", "FAILED", "ERROR", "INVALID"}
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    max_age = timedelta(days=max_age_days)

    packet_ids: list[str] = []
    packet_statuses: list[str] = []
    packet_run_ids: set[str] = set()
    valid_packet_count = 0
    invalid_packet_count = 0
    stale_packet_count = 0

    for packet in packets:
        if not isinstance(packet, dict):
            errors.append("remote_evidence_packet_invalid")
            continue
        packet_id = str(packet.get("packet_id", "")).strip()
        packet_ref = str(packet.get("ref", "")).strip()
        packet_status = str(packet.get("status", "")).strip().upper()
        packet_run_id = str(packet.get("run_id", manifest_run_id)).strip()

        if not packet_id:
            errors.append("remote_evidence_packet_id_missing")
        if not packet_ref:
            errors.append("remote_evidence_packet_ref_missing")
        if manifest_schema == "RemoteEvidenceManifest.v1" and not packet_run_id:
            errors.append("remote_evidence_packet_run_id_missing")

        observed_at = _parse_timestamp(str(packet.get("observed_at", "")))
        if manifest_schema == "RemoteEvidenceManifest.v1" and observed_at is None:
            errors.append("remote_evidence_packet_observed_at_invalid")

        if packet_status in valid_statuses:
            valid_packet_count += 1
            if observed_at is not None and current - observed_at > max_age:
                stale_packet_count += 1
        elif packet_status in invalid_statuses:
            invalid_packet_count += 1
        else:
            errors.append("remote_evidence_packet_status_unknown")

        if packet_id:
            packet_ids.append(packet_id)
        if packet_status:
            packet_statuses.append(packet_status)
        if packet_run_id:
            packet_run_ids.add(packet_run_id)

    inconsistent = (valid_packet_count > 0 and invalid_packet_count > 0) or len(packet_run_ids) > 1
    if len(packet_run_ids) > 1:
        errors.append("remote_evidence_packet_run_id_inconsistent")

    if errors:
        status = RemoteEvidenceStatus.MALFORMED
    elif inconsistent:
        status = RemoteEvidenceStatus.INCONSISTENT
    elif valid_packet_count == 0 and invalid_packet_count > 0:
        status = RemoteEvidenceStatus.PARTIAL
    elif stale_packet_count == valid_packet_count and valid_packet_count > 0:
        status = RemoteEvidenceStatus.STALE
    elif stale_packet_count > 0:
        status = RemoteEvidenceStatus.PARTIAL
    elif valid_packet_count == len(packets):
        status = RemoteEvidenceStatus.VALID
    else:
        status = RemoteEvidenceStatus.PARTIAL

    return RemoteEvidenceResult(
        status=status,
        manifest_path=manifest_path.as_posix(),
        manifest_id=manifest_id,
        manifest_schema=manifest_schema,
        origin=origin,
        run_id=manifest_run_id,
        packet_ids=sorted(set(packet_ids)),
        packet_count=len(packets),
        valid_packet_count=valid_packet_count,
        invalid_packet_count=invalid_packet_count,
        stale_packet_count=stale_packet_count,
        inconsistent=inconsistent,
        errors=sorted(set(errors)),
    )
