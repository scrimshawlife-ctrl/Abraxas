"""
PolicySnapshot.v0 — Immutable snapshot of policy state at tick time.

When policy changes later, artifacts retain provenance pointing to
the exact policy that governed them at emission time.

Mechanics:
- On first tick for a run_id, write:
    policy_snapshots/<run_id>/retention.<sha256>.policysnapshot.json
- PolicyRef then references:
    snapshot path + sha256 (stable forever)

This is a runtime-only change. No ERS modifications needed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Tuple


def _stable_json_bytes(obj: Dict[str, Any]) -> bytes:
    """Create deterministic JSON bytes for hashing."""
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return s.encode("utf-8")


def _sha256_hex(b: bytes) -> str:
    """Compute SHA-256 hex digest of bytes."""
    return hashlib.sha256(b).hexdigest()


def _read_json(path: Path) -> Dict[str, Any]:
    """Read and parse JSON from path."""
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_policy_snapshot(
    *,
    artifacts_dir: str,
    run_id: str,
    policy_name: str,
    policy_path: str,
    portable: bool = True,
) -> Tuple[str, str]:
    """
    Write (or reuse) an immutable PolicySnapshot.v0 for the given policy file.

    The snapshot is content-addressed: same policy content → same snapshot file.
    This means multiple runs can share the same snapshot if policy hasn't changed.

    Args:
        artifacts_dir: Root directory for artifacts
        run_id: Run identifier for snapshot directory scoping
        policy_name: Name of the policy (e.g., "retention")
        policy_path: Path to the source policy file
        portable: If True (default), use relative paths for determinism across environments

    Returns:
        Tuple of (snapshot_path_pattern, snapshot_sha256)
        - snapshot_path_pattern: relative path pattern if portable=True, else absolute path
    """
    root = Path(artifacts_dir)
    p = Path(policy_path)

    # Use relative source_path pattern for determinism
    # This ensures same policy content → same hash across environments
    source_pattern = f"policy/{policy_name}.json"

    # Relative path pattern for the snapshot itself
    rel_pattern = f"policy_snapshots/{run_id}/{policy_name}.{{h}}.policysnapshot.json"

    if not p.exists():
        # No policy file: snapshot still exists, but marked missing deterministically.
        snap_obj = {
            "schema": "PolicySnapshot.v0",
            "policy": policy_name,
            "present": False,
            "source_path_pattern": source_pattern,
            "policy_obj": None,
        }
        b = _stable_json_bytes(snap_obj)
        h = _sha256_hex(b)
        rel_path = f"policy_snapshots/{run_id}/{policy_name}.{h}.policysnapshot.json"
        out = root / "policy_snapshots" / run_id / f"{policy_name}.{h}.policysnapshot.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        if not out.exists():
            out.write_bytes(b)
        return (rel_path if portable else str(out)), h

    pol = _read_json(p)
    snap_obj = {
        "schema": "PolicySnapshot.v0",
        "policy": policy_name,
        "present": True,
        "source_path_pattern": source_pattern,
        "policy_obj": pol,
    }
    b = _stable_json_bytes(snap_obj)
    h = _sha256_hex(b)
    rel_path = f"policy_snapshots/{run_id}/{policy_name}.{h}.policysnapshot.json"
    out = root / "policy_snapshots" / run_id / f"{policy_name}.{h}.policysnapshot.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    if not out.exists():
        out.write_bytes(b)
    return (rel_path if portable else str(out)), h


def policy_ref_from_snapshot(
    policy: str,
    snapshot_path: str,
    snapshot_sha256: str,
) -> Dict[str, Any]:
    """
    Create a PolicyRef.v0 that points to an immutable snapshot.

    Unlike the original PolicyRef that points to the mutable policy file,
    this version points to a snapshot that can never change.

    Args:
        policy: Name of the policy (e.g., "retention")
        snapshot_path: Path to the snapshot file
        snapshot_sha256: SHA-256 hash of the snapshot content

    Returns:
        PolicyRef.v0 dict with snapshot reference
    """
    return {
        "schema": "PolicyRef.v0",
        "policy": policy,
        "snapshot_path": snapshot_path,
        "snapshot_sha256": snapshot_sha256,
    }


def resolve_snapshot_path(
    snapshot_path_pattern: str,
    artifacts_dir: str | None = None,
) -> Path:
    """
    Resolve a snapshot path pattern to an absolute path.

    Args:
        snapshot_path_pattern: Relative pattern or absolute path
        artifacts_dir: Base directory for resolving relative patterns

    Returns:
        Resolved absolute Path
    """
    p = Path(snapshot_path_pattern)
    if p.is_absolute():
        return p
    if artifacts_dir:
        return Path(artifacts_dir) / snapshot_path_pattern
    return p


def load_policy_snapshot(
    snapshot_path: str,
    artifacts_dir: str | None = None,
) -> Dict[str, Any]:
    """
    Load and return a PolicySnapshot.v0 from disk.

    Args:
        snapshot_path: Path to the snapshot file (can be relative pattern)
        artifacts_dir: Base directory for resolving relative patterns

    Returns:
        PolicySnapshot.v0 dict

    Raises:
        FileNotFoundError: If snapshot file doesn't exist
        ValueError: If snapshot has invalid schema
    """
    p = resolve_snapshot_path(snapshot_path, artifacts_dir)
    if not p.exists():
        raise FileNotFoundError(f"Snapshot not found: {snapshot_path}")

    snap = _read_json(p)
    if snap.get("schema") != "PolicySnapshot.v0":
        raise ValueError(f"Invalid snapshot schema: {snap.get('schema')}")

    return snap


def verify_policy_snapshot(
    snapshot_path: str,
    expected_sha256: str,
    artifacts_dir: str | None = None,
) -> Dict[str, Any]:
    """
    Verify a snapshot file matches its expected hash.

    Args:
        snapshot_path: Path to the snapshot file (can be relative pattern)
        expected_sha256: Expected SHA-256 hash
        artifacts_dir: Base directory for resolving relative patterns

    Returns:
        Verification result dict with:
        - valid: boolean
        - reason: explanation
        - actual_sha256: computed hash (or None if missing)
    """
    p = resolve_snapshot_path(snapshot_path, artifacts_dir)
    if not p.exists():
        return {
            "valid": False,
            "reason": f"Snapshot file missing: {snapshot_path}",
            "actual_sha256": None,
        }

    b = p.read_bytes()
    actual = _sha256_hex(b)

    if actual == expected_sha256:
        return {
            "valid": True,
            "reason": "Snapshot hash matches",
            "actual_sha256": actual,
        }
    else:
        return {
            "valid": False,
            "reason": f"Snapshot hash mismatch: expected {expected_sha256}, got {actual}",
            "actual_sha256": actual,
        }


__all__ = [
    "ensure_policy_snapshot",
    "policy_ref_from_snapshot",
    "resolve_snapshot_path",
    "load_policy_snapshot",
    "verify_policy_snapshot",
]
