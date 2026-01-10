from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


@dataclass(frozen=True)
class TermControl:
    term_id: str
    modulation_depth: float
    lfo_rate: float
    filter_slope: float
    pitch_bias: float


@dataclass(frozen=True)
class BeatOvenFrame:
    terms: List[TermControl]
    volatility: float
    velocity_scale: float
    tempo_shift_bpm: float
    symbolic_load_cc: float


def map_aalmanac_terms(terms: Iterable[Dict[str, Any]]) -> List[TermControl]:
    mapped: List[TermControl] = []
    for term in terms:
        drift = float(term.get("drift_charge", 0.0) or 0.0)
        half_life = float(term.get("half_life", 1.0) or 1.0)
        direction = term.get("directionality", "oscillatory")

        modulation_depth = _clamp(drift, 0.0, 1.0)
        lfo_rate = _clamp(1.0 / max(1.0, half_life / 10.0), 0.05, 2.0)

        if direction == "+":
            filter_slope = 1.0
            pitch_bias = 0.2
        elif direction == "-":
            filter_slope = -1.0
            pitch_bias = -0.2
        else:
            filter_slope = 0.0
            pitch_bias = 0.0

        mapped.append(
            TermControl(
                term_id=str(term.get("term_id", "")),
                modulation_depth=modulation_depth,
                lfo_rate=lfo_rate,
                filter_slope=filter_slope,
                pitch_bias=pitch_bias,
            )
        )
    return mapped


def map_semiotic_weather(weather: Dict[str, Any]) -> Dict[str, float]:
    volatility_index = float(weather.get("volatility_index", 0.0) or 0.0)
    compression_ratio = float(weather.get("compression_ratio", 1.0) or 1.0)

    volatility = _clamp(volatility_index / 100.0, 0.0, 1.0)
    velocity_scale = _clamp(1.0 / max(0.1, compression_ratio), 0.2, 1.0)

    return {
        "volatility": volatility,
        "velocity_scale": velocity_scale,
    }


def map_oracle_context(context: Dict[str, Any]) -> Dict[str, float]:
    kairos = str(context.get("kairos_window", "open"))
    ritual_density = float(context.get("ritual_density", 0.0) or 0.0)
    symbolic_load = float(context.get("symbolic_load", 0.0) or 0.0)

    if kairos == "open":
        tempo_shift = 2.0
    elif kairos == "narrowing":
        tempo_shift = -2.0
    else:
        tempo_shift = 0.0

    return {
        "tempo_shift_bpm": tempo_shift,
        "symbolic_load_cc": _clamp(symbolic_load, 0.0, 1.0),
        "ritual_density": _clamp(ritual_density, 0.0, 1.0),
    }


def build_control_frame(
    *,
    terms: Iterable[Dict[str, Any]],
    semiotic_weather: Dict[str, Any],
    oracle_context: Dict[str, Any],
) -> BeatOvenFrame:
    term_controls = map_aalmanac_terms(terms)
    weather_controls = map_semiotic_weather(semiotic_weather)
    oracle_controls = map_oracle_context(oracle_context)

    return BeatOvenFrame(
        terms=term_controls,
        volatility=weather_controls["volatility"],
        velocity_scale=weather_controls["velocity_scale"],
        tempo_shift_bpm=oracle_controls["tempo_shift_bpm"],
        symbolic_load_cc=oracle_controls["symbolic_load_cc"],
    )
