"""ABX-ACTIVE_POINTER_ATOMIC rune operator."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def apply_active_pointer_atomic(*, path: str, strict_execution: bool = True) -> Dict[str, Any]:
    pointer = Path(path)
    if not pointer.parent.exists():
        pointer.parent.mkdir(parents=True, exist_ok=True)
    if not pointer.parent.exists():
        raise ValueError("Pointer directory not writable.")
    return {"path": str(pointer), "atomic_ready": True}
