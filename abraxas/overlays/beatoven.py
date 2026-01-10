from __future__ import annotations
from typing import Dict, Any, List
from .base import AbraxasOverlay, OverlayMeta
from ..core.state import OracleState
from ..core.context import UserContext


class BeatOvenOverlay(AbraxasOverlay):
    meta = OverlayMeta(
        name="beatoven",
        version="v0.1.0",
        required_signals=("pressure",),
        output_schema="schemas/beatoven_output.v0.json",
    )

    def run(self, oracle_state: OracleState, user: UserContext) -> Dict[str, Any]:
        # Deterministic sonification mapping placeholder
        pressure = float(oracle_state.symbolic_layer.get("pressure", 0) or 0)
        tempo = int(90 + min(60, pressure * 8))  # 90..150
        scale = "Dorian" if pressure >= 6 else "Major"
        chords = ["i", "bVII", "bVI", "bVII"] if scale == "Dorian" else ["I", "V", "vi", "IV"]

        return {
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
                "coherence": oracle_state.metric_layer.get("coherence"),
            }
        }
