"""ABX-OFFLINE_ENFORCE rune operator."""

from __future__ import annotations

from typing import Any, Dict


def apply_offline_enforce(*, offline: bool, strict_execution: bool = True) -> Dict[str, Any]:
    if not offline:
        raise ValueError("Offline profiling required unless explicitly allowed.")
    return {"offline": True}
