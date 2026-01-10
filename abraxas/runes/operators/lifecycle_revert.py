"""ABX-LIFECYCLE_REVERT rune operator."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def apply_lifecycle_revert(
    *,
    pointer_path: str,
    strict_execution: bool = True,
) -> Dict[str, Any]:
    pointer = Path(pointer_path)
    backup = pointer.with_suffix(".bak")
    if not backup.exists():
        return {"reverted": False, "reason": "backup_missing"}
    backup.replace(pointer)
    return {"reverted": True, "path": str(pointer)}
