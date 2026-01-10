"""
Stability Reader — Utility to read RunStability without ref-chasing logic.

This module provides a simple interface for UIs/tools to read stability records
without re-implementing the resolution order:
  1. StabilityRef.v0 → RunStability.v0
  2. Direct RunStability.v0

Usage:
    from abraxas.runtime.stability_read import read_run_stability

    st = read_run_stability("./artifacts", "my_run")
    if st:
        print(st["ok"], st.get("divergence"))
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


def _read_json(p: Path) -> Dict[str, Any]:
    """Read JSON file and return dict."""
    return json.loads(p.read_text(encoding="utf-8"))


def read_run_stability(artifacts_dir: str, run_id: str) -> Optional[Dict[str, Any]]:
    """
    Read RunStability.v0 for a run if present.

    Resolution order:
      1. runs/<run_id>.stability_ref.json -> runs/<run_id>.runstability.json
      2. runs/<run_id>.runstability.json directly

    Args:
        artifacts_dir: Root directory for artifacts
        run_id: Run identifier

    Returns:
        RunStability.v0 dict or None if not found/invalid
    """
    root = Path(artifacts_dir)
    ref_path = root / "runs" / f"{run_id}.stability_ref.json"
    direct_path = root / "runs" / f"{run_id}.runstability.json"

    # Try via StabilityRef first
    if ref_path.exists():
        try:
            ref = _read_json(ref_path)
            if ref.get("schema") == "StabilityRef.v0":
                stability_path = ref.get("runstability_path")
                if isinstance(stability_path, str) and Path(stability_path).exists():
                    stability = _read_json(Path(stability_path))
                    if stability.get("schema") == "RunStability.v0":
                        return stability
        except Exception:
            # Utility should be non-fatal: return None on malformed refs
            pass

    # Fallback to direct path
    if direct_path.exists():
        try:
            stability = _read_json(direct_path)
            if stability.get("schema") == "RunStability.v0":
                return stability
        except Exception:
            pass

    return None


def read_stability_summary(artifacts_dir: str, run_id: str) -> Optional[Dict[str, Any]]:
    """
    Read a compact stability summary for embedding in ViewPack.

    Returns a small dict suitable for inline embedding:
      - ok: bool
      - first_mismatch_run: int or None
      - divergence_kind: str or None

    Args:
        artifacts_dir: Root directory for artifacts
        run_id: Run identifier

    Returns:
        Compact summary dict or None if not found
    """
    stability = read_run_stability(artifacts_dir, run_id)
    if stability is None:
        return None

    divergence = stability.get("divergence")
    divergence_kind = None
    if isinstance(divergence, dict):
        divergence_kind = divergence.get("kind")

    return {
        "schema": "StabilitySummary.v0",
        "ok": stability.get("ok"),
        "first_mismatch_run": stability.get("first_mismatch_run"),
        "divergence_kind": divergence_kind,
    }


def stability_exists(artifacts_dir: str, run_id: str) -> bool:
    """
    Check if stability record exists for a run.

    Args:
        artifacts_dir: Root directory for artifacts
        run_id: Run identifier

    Returns:
        True if stability record exists and is valid
    """
    return read_run_stability(artifacts_dir, run_id) is not None


__all__ = [
    "read_run_stability",
    "read_stability_summary",
    "stability_exists",
]
