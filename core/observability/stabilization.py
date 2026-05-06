"""StabilizationTelemetry.v1

Tracks replay stability across multiple execution runs.
replay_failures must not exceed replay_count (fail-closed).
"""
from __future__ import annotations

import hashlib
import json
from typing import Optional

from core.models.governance import Authority


_SCHEMA_VERSION = "StabilizationTelemetry.v1"

VALID_STATES = frozenset({"not_started", "active", "stable", "unstable", "failed"})


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class StabilizationTelemetry:
    """Replay stabilization telemetry for governed execution.

    Fields
    ------
    schema_version             Fixed at "StabilizationTelemetry.v1"
    stabilization_id           Unique identifier
    execution_hash             Hash of the execution being stabilized
    replay_count               Total number of replays attempted
    deterministic_replay_matches  Number of replays that matched exactly
    replay_failures            Number of replay failures (must <= replay_count)
    route_failures             Number of route failures observed
    authority                  Locked Authority token
    stabilization_state        One of: not_started|active|stable|unstable|failed
    """

    schema_version: str = _SCHEMA_VERSION

    def __init__(
        self,
        *,
        stabilization_id: str,
        execution_hash: str,
        replay_count: int,
        deterministic_replay_matches: int,
        replay_failures: int,
        route_failures: int,
        authority: Authority,
        stabilization_state: str = "not_started",
    ) -> None:
        if not authority.is_locked():
            raise ValueError("authority must be locked")
        if stabilization_state not in VALID_STATES:
            raise ValueError(
                f"stabilization_state must be one of {sorted(VALID_STATES)}, "
                f"got {stabilization_state!r}"
            )
        if replay_count < 0:
            raise ValueError("replay_count must be non-negative")
        if deterministic_replay_matches < 0:
            raise ValueError("deterministic_replay_matches must be non-negative")
        if replay_failures < 0:
            raise ValueError("replay_failures must be non-negative")
        if replay_failures > replay_count:
            raise ValueError(
                f"replay_failures ({replay_failures}) cannot exceed "
                f"replay_count ({replay_count})"
            )
        if route_failures < 0:
            raise ValueError("route_failures must be non-negative")

        self.schema_version = _SCHEMA_VERSION
        self.stabilization_id = stabilization_id
        self.execution_hash = execution_hash
        self.replay_count = replay_count
        self.deterministic_replay_matches = deterministic_replay_matches
        self.replay_failures = replay_failures
        self.route_failures = route_failures
        self.authority = authority
        self.stabilization_state = stabilization_state

    def telemetry_hash(self) -> str:
        payload = {
            "schema_version": self.schema_version,
            "stabilization_id": self.stabilization_id,
            "execution_hash": self.execution_hash,
            "replay_count": self.replay_count,
            "deterministic_replay_matches": self.deterministic_replay_matches,
            "replay_failures": self.replay_failures,
            "route_failures": self.route_failures,
            "stabilization_state": self.stabilization_state,
        }
        return _sha256(_canonical(payload))

    def is_stable(self) -> bool:
        return self.stabilization_state == "stable"

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "stabilization_id": self.stabilization_id,
            "execution_hash": self.execution_hash,
            "replay_count": self.replay_count,
            "deterministic_replay_matches": self.deterministic_replay_matches,
            "replay_failures": self.replay_failures,
            "route_failures": self.route_failures,
            "authority": self.authority.to_dict(),
            "stabilization_state": self.stabilization_state,
            "telemetry_hash": self.telemetry_hash(),
        }


def build_stabilization_telemetry(
    *,
    stabilization_id: str,
    execution_hash: str,
    replay_count: int,
    deterministic_replay_matches: int,
    replay_failures: int,
    route_failures: int,
    authority: Optional[Authority] = None,
    stabilization_state: str = "not_started",
) -> StabilizationTelemetry:
    """Factory for StabilizationTelemetry."""
    if authority is None:
        authority = Authority.locked()
    return StabilizationTelemetry(
        stabilization_id=stabilization_id,
        execution_hash=execution_hash,
        replay_count=replay_count,
        deterministic_replay_matches=deterministic_replay_matches,
        replay_failures=replay_failures,
        route_failures=route_failures,
        authority=authority,
        stabilization_state=stabilization_state,
    )
