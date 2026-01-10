"""
RunHeader.v0 — Run-level provenance written once per run_id.

Tick artifacts should stay light. Heavy provenance belongs to the run, not every tick.

RunHeader contains:
- pipeline bindings provenance
- policy snapshot refs (retention)
- optional git sha (best-effort, no failure if missing)
- python + platform fingerprint

Each tick's RunIndex points to this header for full run-level provenance.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


def _stable_json_bytes(obj: Dict[str, Any]) -> bytes:
    """Create deterministic JSON bytes for hashing."""
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return s.encode("utf-8")


def _sha256_hex(b: bytes) -> str:
    """Compute SHA-256 hex digest of bytes."""
    return hashlib.sha256(b).hexdigest()


def _try_git_sha(repo_root: Optional[str] = None) -> Optional[str]:
    """
    Best-effort git SHA. Never raises.

    Args:
        repo_root: Optional path to git repository root

    Returns:
        Git SHA string or None if unavailable
    """
    try:
        cmd = ["git", "rev-parse", "HEAD"]
        out = subprocess.check_output(
            cmd,
            cwd=repo_root or None,
            stderr=subprocess.DEVNULL,
        )
        sha = out.decode("utf-8").strip()
        if sha:
            return sha
    except Exception:
        return None
    return None


def _env_fingerprint() -> Dict[str, Any]:
    """
    Create environment fingerprint for provenance.

    Returns:
        Dict with python and platform information
    """
    return {
        "python": {
            "version": sys.version.split(" ")[0],
            "implementation": platform.python_implementation(),
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
    }


def ensure_run_header(
    *,
    artifacts_dir: str,
    run_id: str,
    mode: str,
    pipeline_bindings_provenance: Dict[str, Any],
    policy_refs: Dict[str, Any],
    repo_root: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Write (or reuse) RunHeader.v0 for run_id.

    Deterministic path:
        <artifacts_dir>/runs/<run_id>.runheader.json

    Contents may include best-effort git SHA; absence is explicit (None).

    Args:
        artifacts_dir: Root directory for artifacts
        run_id: Run identifier
        mode: Execution mode (e.g., "live", "test", "backtest")
        pipeline_bindings_provenance: Provenance dict from pipeline bindings
        policy_refs: Dict of policy name to PolicyRef
        repo_root: Optional path to git repository root

    Returns:
        Tuple of (path, sha256)
    """
    root = Path(artifacts_dir)
    out = root / "runs" / f"{run_id}.runheader.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    # If exists, trust it (do not rewrite) to preserve time continuity.
    if out.exists():
        b = out.read_bytes()
        return str(out), _sha256_hex(b)

    header = {
        "schema": "RunHeader.v0",
        "run_id": run_id,
        "mode": mode,
        "code": {
            "git_sha": _try_git_sha(repo_root=repo_root),
        },
        "pipeline_bindings": pipeline_bindings_provenance,
        "policy_refs": policy_refs,
        # Convention: stability ref pattern (relative to artifacts_dir).
        # RunHeader remains write-once; stability is stored separately.
        # Resolve: {artifacts_dir}/runs/{run_id}.stability_ref.json
        "stability_ref_pattern": f"runs/{run_id}.stability_ref.json",
        "env": _env_fingerprint(),
    }

    b = _stable_json_bytes(header)
    out.write_bytes(b)
    return str(out), _sha256_hex(b)


def load_run_header(run_header_path: str) -> Dict[str, Any]:
    """
    Load and return a RunHeader.v0 from disk.

    Args:
        run_header_path: Path to the run header file

    Returns:
        RunHeader.v0 dict

    Raises:
        FileNotFoundError: If header file doesn't exist
        ValueError: If header has invalid schema
    """
    p = Path(run_header_path)
    if not p.exists():
        raise FileNotFoundError(f"RunHeader not found: {run_header_path}")

    header = json.loads(p.read_text(encoding="utf-8"))
    if header.get("schema") != "RunHeader.v0":
        raise ValueError(f"Invalid run header schema: {header.get('schema')}")

    return header


def verify_run_header(
    run_header_path: str,
    expected_sha256: str,
) -> Dict[str, Any]:
    """
    Verify a run header file matches its expected hash.

    Args:
        run_header_path: Path to the run header file
        expected_sha256: Expected SHA-256 hash

    Returns:
        Verification result dict with:
        - valid: boolean
        - reason: explanation
        - actual_sha256: computed hash (or None if missing)
    """
    p = Path(run_header_path)
    if not p.exists():
        return {
            "valid": False,
            "reason": f"RunHeader file missing: {run_header_path}",
            "actual_sha256": None,
        }

    b = p.read_bytes()
    actual = _sha256_hex(b)

    if actual == expected_sha256:
        return {
            "valid": True,
            "reason": "RunHeader hash matches",
            "actual_sha256": actual,
        }
    else:
        return {
            "valid": False,
            "reason": f"RunHeader hash mismatch: expected {expected_sha256}, got {actual}",
            "actual_sha256": actual,
        }


__all__ = [
    "ensure_run_header",
    "load_run_header",
    "verify_run_header",
]
