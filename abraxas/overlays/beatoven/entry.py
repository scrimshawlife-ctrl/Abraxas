from __future__ import annotations

from typing import Any, Dict

from ...schemas.overlay_packet_v0 import OverlayPacketV0, packet_ok, packet_not_computable


def _pressure_from_inputs(inputs: Any) -> float:
    pressure = 0.0
    signal = getattr(inputs, "tier_ctx", {})
    if isinstance(signal, dict):
        pressure = float(signal.get("limits", {}).get("scenario_branches", 0))
    return max(0.0, min(10.0, pressure * 2.0))


def run_overlay(inputs: Any, ctx: Dict[str, Any]) -> OverlayPacketV0:
    tier = ctx.get("tier_ctx", {}).get("tier", "psychonaut")
    pressure = _pressure_from_inputs(inputs)

    if pressure == 0.0:
        return packet_not_computable("beatoven", "v0.2.0", "Insufficient signal pressure for sonification.")

    tempo = int(90 + min(60, pressure * 8))
    scale = "Dorian" if pressure >= 6 else "Major"
    chords = ["i", "bVII", "bVI", "bVII"] if scale == "Dorian" else ["I", "V", "vi", "IV"]

    data = {
        "tempo": tempo,
        "scale": scale,
        "chords": chords,
        "rhythm_density": "high" if pressure >= 6 else "medium",
        "midi_clips": [
            {"name": "kick", "pattern": "x---x---x---x---"},
            {"name": "snare", "pattern": "----x-------x---"},
        ],
        "cv_gate_map": {
            "clock_hz": tempo / 60.0,
            "gate_pattern": "1010101010101010",
        },
        "emotional_signature": {
            "pressure": pressure,
            "coherence": 0.75,
        },
        "tier": tier,
    }

    metrics = {"pressure": pressure, "tempo": tempo}
    summary = "BeatOven sonification packet (deterministic placeholder)."
    return packet_ok("beatoven", "v0.2.0", summary, data, metrics=metrics)
