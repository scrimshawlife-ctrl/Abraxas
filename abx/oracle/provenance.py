"""Provenance stamping for oracle outputs with ABX-Runes integration."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any, Dict


def load_manifest_sha256() -> str:
    """Load rune manifest and return its SHA256 hash.

    Returns:
        SHA256 hex digest of manifest.json bytes
    """
    manifest_path = Path(__file__).parent.parent.parent / "abraxas/runes/sigils/manifest.json"

    if not manifest_path.exists():
        # Fallback: deterministic placeholder for missing manifest
        return hashlib.sha256(b"manifest_not_found").hexdigest()

    with open(manifest_path, "rb") as f:
        manifest_bytes = f.read()

    return hashlib.sha256(manifest_bytes).hexdigest()


def stamp(
    output: Dict[str, Any],
    runes_used: list[str],
    gate_state: str,
    extras: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Add ABX-Runes provenance stamp to oracle output.

    Args:
        output: Oracle output dict (will be modified in-place)
        runes_used: List of rune IDs (e.g., ["ϟ₁", "ϟ₂", "ϟ₄", "ϟ₅", "ϟ₆"])
        gate_state: SDS gate state ("CLOSED" | "LIMINAL" | "OPEN")
        extras: Additional provenance data (IPL schedule, drift metrics, etc.)

    Returns:
        Modified output dict with "abx_runes" key added
    """
    manifest_sha256 = load_manifest_sha256()

    provenance = {
        "used": runes_used,
        "manifest_sha256": manifest_sha256,
        "gate_state": gate_state,
    }

    if extras:
        provenance.update(extras)

    output["abx_runes"] = provenance
    return output
