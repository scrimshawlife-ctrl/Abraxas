"""
RunStability.v0 — Persist Dozen-Run Gate result for auditing.

This module provides:
- write_run_stability(): Write RunStability.v0 artifact with gate result
- write_stability_ref(): Write StabilityRef.v0 pointer (avoids mutating RunHeader)
- load_run_stability(): Load and validate RunStability.v0
- load_stability_ref(): Load and validate StabilityRef.v0

Design:
  RunHeader is write-once (immutable). We don't want to rewrite it.
  So stability is stored separately:
  - runs/<run_id>.runstability.json (RunStability.v0)
  - runs/<run_id>.stability_ref.json (StabilityRef.v0 - small pointer)

  RunHeader includes a convention path for discoverability:
    stability_ref_path: runs/<run_id>.stability_ref.json

  UIs can:
  1. Load RunHeader.v0
  2. Read stability_ref_path
  3. If file exists, load RunStability.v0 for run-level badge
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


def _stable_json_bytes(obj: Dict[str, Any]) -> bytes:
    """Create deterministic JSON bytes for hashing."""
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return s.encode("utf-8")


def _sha256_hex(b: bytes) -> str:
    """Compute SHA-256 hex digest of bytes."""
    return hashlib.sha256(b).hexdigest()


def write_run_stability(
    *,
    artifacts_dir: str,
    run_id: str,
    gate_result: Dict[str, Any],
    note: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Write RunStability.v0 artifact.

    Path: <artifacts_dir>/runs/<run_id>.runstability.json

    Overwrites are allowed (this is a "latest known stability" record),
    but the content is deterministic JSON.

    Args:
        artifacts_dir: Root directory for artifacts
        run_id: Run identifier
        gate_result: Result dict from dozen_run_tick_invariance_gate
            Expected keys: ok, expected_sha256, sha256s, expected_runheader_sha256,
                          runheader_sha256s, first_mismatch_run, divergence
        note: Optional note (e.g., "dozen-run gate pass")

    Returns:
        Tuple of (path, sha256)
    """
    root = Path(artifacts_dir)
    out = root / "runs" / f"{run_id}.runstability.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    obj = {
        "schema": "RunStability.v0",
        "run_id": run_id,
        "ok": bool(gate_result.get("ok")),
        "expected_trendpack_sha256": gate_result.get("expected_sha256"),
        "trendpack_sha256s": gate_result.get("sha256s"),
        "expected_runheader_sha256": gate_result.get("expected_runheader_sha256"),
        "runheader_sha256s": gate_result.get("runheader_sha256s"),
        "first_mismatch_run": gate_result.get("first_mismatch_run"),
        "divergence": gate_result.get("divergence"),
        "note": note,
    }

    b = _stable_json_bytes(obj)
    out.write_bytes(b)
    return str(out), _sha256_hex(b)


def write_stability_ref(
    *,
    artifacts_dir: str,
    run_id: str,
    runstability_path: str,
    runstability_sha256: str,
) -> Tuple[str, str]:
    """
    Write StabilityRef.v0 pointer file (avoids rewriting RunHeader).

    Path: <artifacts_dir>/runs/<run_id>.stability_ref.json

    Args:
        artifacts_dir: Root directory for artifacts
        run_id: Run identifier
        runstability_path: Path to RunStability.v0 file
        runstability_sha256: SHA-256 of RunStability.v0 content

    Returns:
        Tuple of (path, sha256)
    """
    root = Path(artifacts_dir)
    out = root / "runs" / f"{run_id}.stability_ref.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    obj = {
        "schema": "StabilityRef.v0",
        "run_id": run_id,
        "runstability_path": runstability_path,
        "runstability_sha256": runstability_sha256,
    }

    b = _stable_json_bytes(obj)
    out.write_bytes(b)
    return str(out), _sha256_hex(b)


def load_run_stability(run_stability_path: str) -> Dict[str, Any]:
    """
    Load and return a RunStability.v0 from disk.

    Args:
        run_stability_path: Path to the run stability file

    Returns:
        RunStability.v0 dict

    Raises:
        FileNotFoundError: If stability file doesn't exist
        ValueError: If stability has invalid schema
    """
    p = Path(run_stability_path)
    if not p.exists():
        raise FileNotFoundError(f"RunStability not found: {run_stability_path}")

    stability = json.loads(p.read_text(encoding="utf-8"))
    if stability.get("schema") != "RunStability.v0":
        raise ValueError(f"Invalid run stability schema: {stability.get('schema')}")

    return stability


def load_stability_ref(stability_ref_path: str) -> Dict[str, Any]:
    """
    Load and return a StabilityRef.v0 from disk.

    Args:
        stability_ref_path: Path to the stability ref file

    Returns:
        StabilityRef.v0 dict

    Raises:
        FileNotFoundError: If ref file doesn't exist
        ValueError: If ref has invalid schema
    """
    p = Path(stability_ref_path)
    if not p.exists():
        raise FileNotFoundError(f"StabilityRef not found: {stability_ref_path}")

    ref = json.loads(p.read_text(encoding="utf-8"))
    if ref.get("schema") != "StabilityRef.v0":
        raise ValueError(f"Invalid stability ref schema: {ref.get('schema')}")

    return ref


def verify_run_stability(
    run_stability_path: str,
    expected_sha256: str,
) -> Dict[str, Any]:
    """
    Verify a run stability file matches its expected hash.

    Args:
        run_stability_path: Path to the run stability file
        expected_sha256: Expected SHA-256 hash

    Returns:
        Verification result dict with:
        - valid: boolean
        - reason: explanation
        - actual_sha256: computed hash (or None if missing)
    """
    p = Path(run_stability_path)
    if not p.exists():
        return {
            "valid": False,
            "reason": f"RunStability file missing: {run_stability_path}",
            "actual_sha256": None,
        }

    b = p.read_bytes()
    actual = _sha256_hex(b)

    if actual == expected_sha256:
        return {
            "valid": True,
            "reason": "RunStability hash matches",
            "actual_sha256": actual,
        }
    else:
        return {
            "valid": False,
            "reason": f"RunStability hash mismatch: expected {expected_sha256}, got {actual}",
            "actual_sha256": actual,
        }


def get_stability_ref_path(artifacts_dir: str, run_id: str) -> str:
    """
    Get convention path for StabilityRef.v0.

    This is the path that RunHeader.v0 will reference for discoverability.

    Args:
        artifacts_dir: Root directory for artifacts
        run_id: Run identifier

    Returns:
        Path to stability ref file (may not exist yet)
    """
    root = Path(artifacts_dir)
    return str(root / "runs" / f"{run_id}.stability_ref.json")


__all__ = [
    "write_run_stability",
    "write_stability_ref",
    "load_run_stability",
    "load_stability_ref",
    "verify_run_stability",
    "get_stability_ref_path",
]
