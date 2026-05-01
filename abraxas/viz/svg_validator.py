from __future__ import annotations

from typing import Any, Dict

from abraxas.viz.svg_models import AUTHORITY_FLAGS


def validate_render_authority() -> None:
    if AUTHORITY_FLAGS.get("inference") is not False:
        raise ValueError("inference must be false")
    if AUTHORITY_FLAGS.get("production_activation") is not False:
        raise ValueError("production_activation must be false")


def validate_view_packet(view_packet: Dict[str, Any]) -> None:
    if not isinstance(view_packet, dict):
        raise TypeError("view packet must be object")
    for key in ("nodes", "edges", "alerts", "actions"):
        value = view_packet.get(key)
        if value is None:
            continue
        if not isinstance(value, list):
            raise TypeError(f"{key} must be list")
