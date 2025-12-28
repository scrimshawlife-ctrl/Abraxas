"""Symbolic Pressure Index (SPI) — system stress field detector.

Concept: High latency variance + high error rate = pressure.
Pressure ≠ failure. Pressure = stress field.

Feeds memetic weather and system tension models.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from abx.intel_bridge import load, emit


def main() -> None:
    """Generate symbolic pressure index from telemetry."""
    latency = load("latency_baselines.json")
    confidence = load("confidence_decay.json")

    pressure: dict[str, dict[str, float]] = {}

    for rid, lat in latency.items():
        conf = confidence.get(rid, {})
        err = conf.get("error_rate", 0.0)

        # Latency spread as pressure indicator
        # High p95-p50 spread = high variance = instability
        latency_spread = 0.0
        p95 = lat.get("p95_ns")
        p50 = lat.get("p50_ns")
        if p95 and p50 and p50 > 0:
            latency_spread = (p95 - p50) / p50

        # Combine latency variance with error rate
        # Pressure = latency_spread + error_rate (capped at 1.0)
        pressure_score = min(1.0, latency_spread + err)

        pressure[rid] = {
            "latency_spread": round(latency_spread, 4),
            "error_rate": round(err, 4),
            "pressure_score": round(pressure_score, 4),
            "pressure_class": _classify_pressure(pressure_score),
        }

    # Emit intelligence artifact
    path = emit("symbolic_pressure.json", pressure)
    print(f"Symbolic pressure index written to: {path}")
    print(f"Analyzed {len(pressure)} runes")

    # Console summary
    if pressure:
        high_pressure = [
            (rid, p["pressure_score"])
            for rid, p in pressure.items()
            if p["pressure_score"] > 0.5
        ]
        if high_pressure:
            print("\nHigh pressure runes:")
            for rid, score in sorted(high_pressure, key=lambda x: -x[1]):
                pclass = pressure[rid]["pressure_class"]
                print(f"  {rid}: {score:.3f} ({pclass})")


def _classify_pressure(score: float) -> str:
    """Classify pressure level."""
    if score >= 0.8:
        return "critical"
    elif score >= 0.5:
        return "high"
    elif score >= 0.3:
        return "moderate"
    elif score >= 0.1:
        return "low"
    else:
        return "minimal"


if __name__ == "__main__":
    main()
