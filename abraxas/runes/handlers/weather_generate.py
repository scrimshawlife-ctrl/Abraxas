"""Kernel handler for weather.generate rune."""

from __future__ import annotations

from typing import Any, Dict, List

from shared.evidence import sha256_obj
from abraxas.weather.registry import classify_weather


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def generate_weather(payload: Dict[str, Any]) -> Dict[str, Any]:
    compression_event = payload.get("compression_event") or {}
    time_window = payload.get("time_window") or {}
    config = payload.get("config") or {}

    if not compression_event:
        return {
            "weather_report": {},
            "drift_vectors": {},
            "provenance_bundle": {
                "inputs_sha256": sha256_obj(payload),
                "handler": "weather.generate",
                "plan_only": True,
            },
            "not_computable": {
                "reason": "missing compression_event",
                "missing_inputs": ["compression_event"],
                "provenance": {"inputs_sha256": sha256_obj(payload)},
            },
        }

    compression_pressure = _float(compression_event.get("compression_pressure"), 0.0)
    observed_frequency = _float(compression_event.get("observed_frequency"), 0.0)
    half_life_per_event = _float(config.get("half_life_per_event_hours"), 6.0)

    tau_velocity = compression_pressure
    tau_half_life = max(0.0, observed_frequency * half_life_per_event)

    weather_types = classify_weather(tau_velocity=tau_velocity, tau_half_life=tau_half_life)
    weather_codes = [w.value for w in weather_types]

    report = {
        "domain": compression_event.get("domain") or "unknown",
        "window": time_window,
        "tau_velocity": round(tau_velocity, 6),
        "tau_half_life": round(tau_half_life, 6),
        "weather_types": weather_codes,
        "primary_weather": weather_codes[0] if weather_codes else None,
    }

    drift_vectors = compression_event.get("replacement_direction_vector") or {}
    if not isinstance(drift_vectors, dict):
        drift_vectors = {}

    return {
        "weather_report": report,
        "drift_vectors": drift_vectors,
        "provenance_bundle": {
            "inputs_sha256": sha256_obj(payload),
            "handler": "weather.generate",
        },
    }
