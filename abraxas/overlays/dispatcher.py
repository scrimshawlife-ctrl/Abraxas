from __future__ import annotations

import importlib
from typing import Any, Dict, Callable, Optional, Tuple

from ..schemas.overlay_packet_v0 import (
    OverlayPacketV0,
    packet_ok,
    packet_disabled,
    packet_not_installed,
    packet_not_computable,
    packet_error,
)


OVERLAY_REGISTRY: Dict[str, str] = {
    "aalmanac": "abraxas.overlays.aalmanac.entry",
    "neon_genie": "abraxas.overlays.neon_genie.entry",
    "semiotic_weather": "abraxas.overlays.semiotic_weather.entry",
    "memetic_weather": "abraxas.overlays.memetic_weather.entry",
    "financials_plus": "abraxas.overlays.financials_plus.entry",
    "beatoven": "abraxas.overlays.beatoven.entry",
}


def _load_runner(module_path: str) -> Tuple[Optional[Callable[..., Any]], Optional[str]]:
    try:
        mod = importlib.import_module(module_path)
        fn = getattr(mod, "run_overlay", None)
        if not callable(fn):
            return None, f"Missing callable run_overlay in {module_path}"
        return fn, None
    except ModuleNotFoundError as e:
        return None, f"Module not installed: {e}"
    except Exception as e:
        return None, f"Import error: {e}"


def run_overlay_safe(
    overlay_name: str,
    inputs: Any,
    ctx: Dict[str, Any],
    enabled: bool,
) -> OverlayPacketV0:
    module_path = OVERLAY_REGISTRY.get(overlay_name)
    version = "0.1.0"

    if not module_path:
        return packet_not_installed(overlay_name, version, "Overlay not registered.")

    if not enabled:
        return packet_disabled(overlay_name, version, "Disabled by config.")

    fn, err = _load_runner(module_path)
    if fn is None:
        if err and err.startswith("Module not installed"):
            return packet_not_installed(overlay_name, version, err)
        return packet_error(overlay_name, version, err or "Unknown overlay import failure")

    try:
        pkt = fn(inputs, ctx)
        if isinstance(pkt, OverlayPacketV0):
            return pkt
        if isinstance(pkt, dict) and pkt.get("schema") == "overlay_packet.v0":
            return OverlayPacketV0(
                schema="overlay_packet.v0",
                name=pkt.get("name", overlay_name),
                version=pkt.get("version", version),
                status=pkt.get("status", "ok"),
                summary=pkt.get("summary", ""),
                evidence=pkt.get("evidence", []),
                data=pkt.get("data", {}),
                metrics=pkt.get("metrics", {}),
                notes=pkt.get("notes", []),
            )
        return packet_error(overlay_name, version, "Overlay returned invalid packet type.")
    except Exception as e:
        return packet_error(overlay_name, version, repr(e))
