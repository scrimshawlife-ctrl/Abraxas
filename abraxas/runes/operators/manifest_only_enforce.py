"""ABX-MANIFEST_ONLY_ENFORCE rune operator."""

from __future__ import annotations

from typing import Any, Dict


def apply_manifest_only_enforce(
    *,
    stage: str,
    decodo_used: bool,
    strict_execution: bool = True,
) -> Dict[str, Any]:
    allowed = stage == "manifest_discovery"
    if decodo_used and not allowed:
        raise ValueError("Decodo usage is restricted to manifest discovery.")
    return {
        "allowed": allowed or not decodo_used,
        "stage": stage,
        "decodo_used": decodo_used,
    }
