"""Provenance tracking for all OAS operations."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


class ProvenanceRef(BaseModel):
    """Reference to a provenance source with content hash."""

    scheme: str = Field(..., description="Source scheme: file, event, operator, etc.")
    path: str = Field(..., description="Path or identifier within scheme")
    sha256: str = Field(..., description="SHA256 hash of referenced content")

    def __hash__(self) -> int:
        return hash((self.scheme, self.path, self.sha256))


class ProvenanceBundle(BaseModel):
    """Complete provenance record for a transformation or decision."""

    inputs: list[ProvenanceRef] = Field(default_factory=list, description="Input references")
    transforms: list[str] = Field(default_factory=list, description="Ordered list of transform names applied")
    metrics: dict[str, float] = Field(default_factory=dict, description="Metrics computed during this operation")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = Field(default="oasis", description="System or component that created this bundle")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


def hash_canonical_json(obj: Any) -> str:
    """
    Compute stable SHA256 hash of JSON-serializable object.

    Uses canonical JSON encoding: sorted keys, no whitespace, deterministic float repr.
    """
    canonical = json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,  # Convert datetime and other types to string
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def hash_string(s: str) -> str:
    """Compute SHA256 hash of a string."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def hash_bytes(b: bytes) -> str:
    """Compute SHA256 hash of bytes."""
    return hashlib.sha256(b).hexdigest()


@dataclass(frozen=True)
class Provenance:
    """
    Lightweight provenance record for deterministic pipeline runs.
    Used by Lexicon and Oracle systems for tracking execution metadata.
    """

    run_id: str
    started_at_utc: str  # ISO8601 Z
    inputs_hash: str
    config_hash: str
    git_sha: Optional[str] = None
    host: Optional[str] = None

    @staticmethod
    def now_iso_z() -> str:
        """Generate ISO8601 timestamp with Zulu timezone (no microseconds)."""
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_envelope(
    result: Any,
    config: dict,
    inputs: dict,
    operation_id: str,
    seed: Optional[int] = None,
) -> dict[str, Any]:
    """
    Create canonical provenance envelope for rune outputs.

    Standard envelope format enforced across all ABX-Runes capabilities.

    Args:
        result: The actual computation result
        config: Configuration used
        inputs: Input data used
        operation_id: Identifier for the operation (e.g., 'oracle.v2.run')
        seed: Optional deterministic seed

    Returns:
        Dictionary with 'result', 'provenance', and optionally 'not_computable'
    """
    import subprocess
    import platform

    # Get git commit if available
    git_commit = None
    try:
        git_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            timeout=2
        ).decode().strip()
    except Exception:
        pass

    provenance = {
        "timestamp_utc": Provenance.now_iso_z(),
        "config_sha256": hash_canonical_json(config),
        "inputs_sha256": hash_canonical_json(inputs),
        "operation_id": operation_id,
    }

    if git_commit:
        provenance["repo_commit"] = git_commit

    if seed is not None:
        provenance["seed"] = seed

    provenance["runtime_fingerprint"] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
    }

    return {
        "result": result,
        "provenance": provenance,
        "not_computable": None
    }
