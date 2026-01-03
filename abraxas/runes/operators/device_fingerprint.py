"""ABX-DEVICE_FINGERPRINT rune operator."""

from __future__ import annotations

from typing import Any, Dict

from abraxas.runtime.device_fingerprint import get_device_fingerprint


def apply_device_fingerprint(*, run_ctx: Dict[str, Any], strict_execution: bool = True) -> Dict[str, Any]:
    return {"fingerprint": get_device_fingerprint(run_ctx)}
