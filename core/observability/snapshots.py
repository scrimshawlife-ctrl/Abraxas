"""ProjectionStateSnapshot.v1

A projection-only snapshot of the current observability state.
projection_only must always be True.
inference_authority must always be False.
"""
from __future__ import annotations

import hashlib
import json
from typing import Optional

from core.models.governance import Authority


_SCHEMA_VERSION = "ProjectionStateSnapshot.v1"


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class ProjectionStateSnapshot:
    """Projection-only state snapshot.

    This packet is ALWAYS projection_only=True and inference_authority=False.
    Any attempt to set inference_authority=True raises a ValueError (fail-closed).

    Fields
    ------
    schema_version     Fixed at "ProjectionStateSnapshot.v1"
    snapshot_id        Unique identifier
    projection_hash    SHA-256 of the current projection state
    queue_hash         SHA-256 of the current execution queue
    validation_hash    SHA-256 of the validation output
    telemetry_hash     SHA-256 of aggregated telemetry
    topology_hash      SHA-256 of current topology state
    authority          Locked Authority token
    projection_only    Always True
    inference_authority  Always False
    status             "valid" | "authority_violation" | "projection_only_violation" | "failed"
    """

    schema_version: str = _SCHEMA_VERSION

    def __init__(
        self,
        *,
        snapshot_id: str,
        projection_hash: str,
        queue_hash: str,
        validation_hash: str,
        telemetry_hash: str,
        topology_hash: str,
        authority: Authority,
        projection_only: bool = True,
        inference_authority: bool = False,
        status: Optional[str] = None,
    ) -> None:
        if not authority.is_locked():
            raise ValueError("authority must be locked")
        if not projection_only:
            raise ValueError(
                "projection_only must be True — snapshots are always projection-only"
            )
        if inference_authority:
            raise ValueError(
                "inference_authority must be False — snapshots never grant inference authority"
            )

        for name, h in [
            ("projection_hash", projection_hash),
            ("queue_hash", queue_hash),
            ("validation_hash", validation_hash),
            ("telemetry_hash", telemetry_hash),
            ("topology_hash", topology_hash),
        ]:
            if not h:
                raise ValueError(f"{name} must not be empty")

        self.schema_version = _SCHEMA_VERSION
        self.snapshot_id = snapshot_id
        self.projection_hash = projection_hash
        self.queue_hash = queue_hash
        self.validation_hash = validation_hash
        self.telemetry_hash = telemetry_hash
        self.topology_hash = topology_hash
        self.authority = authority
        self.projection_only = True  # forced
        self.inference_authority = False  # forced
        self.status = status or "valid"

    def snapshot_hash(self) -> str:
        payload = {
            "schema_version": self.schema_version,
            "snapshot_id": self.snapshot_id,
            "projection_hash": self.projection_hash,
            "queue_hash": self.queue_hash,
            "validation_hash": self.validation_hash,
            "telemetry_hash": self.telemetry_hash,
            "topology_hash": self.topology_hash,
            "projection_only": self.projection_only,
            "inference_authority": self.inference_authority,
        }
        return _sha256(_canonical(payload))

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "snapshot_id": self.snapshot_id,
            "projection_hash": self.projection_hash,
            "queue_hash": self.queue_hash,
            "validation_hash": self.validation_hash,
            "telemetry_hash": self.telemetry_hash,
            "topology_hash": self.topology_hash,
            "authority": self.authority.to_dict(),
            "projection_only": self.projection_only,
            "inference_authority": self.inference_authority,
            "status": self.status,
            "snapshot_hash": self.snapshot_hash(),
        }


def build_projection_snapshot(
    *,
    snapshot_id: str,
    projection_hash: str,
    queue_hash: str,
    validation_hash: str,
    telemetry_hash: str,
    topology_hash: str,
    authority: Optional[Authority] = None,
) -> ProjectionStateSnapshot:
    """Factory for ProjectionStateSnapshot."""
    if authority is None:
        authority = Authority.locked()
    return ProjectionStateSnapshot(
        snapshot_id=snapshot_id,
        projection_hash=projection_hash,
        queue_hash=queue_hash,
        validation_hash=validation_hash,
        telemetry_hash=telemetry_hash,
        topology_hash=topology_hash,
        authority=authority,
    )
