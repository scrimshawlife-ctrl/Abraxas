"""ReplayTelemetryPacket.v1

Compares receipt chains between an original run and its replay.
If deterministic_match is True, mismatched_receipts must be empty.
"""
from __future__ import annotations

import hashlib
import json
from typing import List, Optional

from core.models.governance import Authority


_SCHEMA_VERSION = "ReplayTelemetryPacket.v1"


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class ReplayTelemetryPacket:
    """Deterministic replay comparison packet.

    Fields
    ------
    schema_version         Fixed at "ReplayTelemetryPacket.v1"
    replay_telemetry_id    Unique identifier
    replay_hash            Hash of the replay run
    compared_receipts      List of receipt IDs compared
    mismatched_receipts    Receipts that differ between original and replay
    deterministic_match    True only when all receipts match exactly
    authority              Locked Authority token
    status                 "valid" | "replay_mismatch" | "authority_violation" | "failed"
    """

    schema_version: str = _SCHEMA_VERSION

    def __init__(
        self,
        *,
        replay_telemetry_id: str,
        replay_hash: str,
        compared_receipts: List[str],
        mismatched_receipts: List[str],
        authority: Authority,
        deterministic_match: Optional[bool] = None,
        status: Optional[str] = None,
    ) -> None:
        if not authority.is_locked():
            raise ValueError("authority must be locked")
        if not replay_hash:
            raise ValueError("replay_hash must not be empty")

        # Consistency: deterministic_match=True requires empty mismatched list
        has_mismatches = bool(mismatched_receipts)
        if deterministic_match is True and has_mismatches:
            raise ValueError(
                "deterministic_match cannot be True when mismatched_receipts is non-empty"
            )

        self.schema_version = _SCHEMA_VERSION
        self.replay_telemetry_id = replay_telemetry_id
        self.replay_hash = replay_hash
        self.compared_receipts = list(compared_receipts)
        self.mismatched_receipts = list(mismatched_receipts)
        self.authority = authority

        # Derive deterministic_match from mismatches if not explicit
        if deterministic_match is not None:
            self.deterministic_match = deterministic_match
        else:
            self.deterministic_match = not has_mismatches

        if status is not None:
            self.status = status
        else:
            self.status = "valid" if self.deterministic_match else "replay_mismatch"

    def packet_hash(self) -> str:
        payload = {
            "schema_version": self.schema_version,
            "replay_telemetry_id": self.replay_telemetry_id,
            "replay_hash": self.replay_hash,
            "compared_receipts": sorted(self.compared_receipts),
            "mismatched_receipts": sorted(self.mismatched_receipts),
            "deterministic_match": self.deterministic_match,
            "status": self.status,
        }
        return _sha256(_canonical(payload))

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "replay_telemetry_id": self.replay_telemetry_id,
            "replay_hash": self.replay_hash,
            "compared_receipts": self.compared_receipts,
            "mismatched_receipts": self.mismatched_receipts,
            "deterministic_match": self.deterministic_match,
            "authority": self.authority.to_dict(),
            "status": self.status,
            "packet_hash": self.packet_hash(),
        }


def build_replay_telemetry(
    *,
    replay_telemetry_id: str,
    replay_hash: str,
    compared_receipts: List[str],
    mismatched_receipts: Optional[List[str]] = None,
    authority: Optional[Authority] = None,
) -> ReplayTelemetryPacket:
    """Factory for ReplayTelemetryPacket."""
    if authority is None:
        authority = Authority.locked()
    return ReplayTelemetryPacket(
        replay_telemetry_id=replay_telemetry_id,
        replay_hash=replay_hash,
        compared_receipts=compared_receipts,
        mismatched_receipts=mismatched_receipts or [],
        authority=authority,
    )
