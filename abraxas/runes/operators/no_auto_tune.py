"""ABX-NO_AUTO_TUNE rune operator."""

from __future__ import annotations

from typing import Any, Dict


def apply_no_auto_tune(*, strict_execution: bool = True) -> Dict[str, Any]:
    return {"selection_only": True}
