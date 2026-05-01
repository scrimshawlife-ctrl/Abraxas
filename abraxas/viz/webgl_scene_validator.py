from __future__ import annotations

from typing import Any, Dict

from abraxas.viz.webgl_scene_models import AUTHORITY


def validate_authority() -> None:
    expected = dict(AUTHORITY)
    if AUTHORITY != expected:
        raise ValueError("authority mismatch")


def validate_input(packet: Dict[str, Any]) -> None:
    if not isinstance(packet, dict):
        raise TypeError("input must be object")
