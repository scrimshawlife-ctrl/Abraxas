#!/usr/bin/env python3
"""
Build Adaptive State Capsules from telemetry and intelligence artifacts.

Offline, deterministic generator that produces per-component state capsules
recording experiential history without mutating runtime behavior.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(".")
INTEL = ROOT / "data" / "intel"
TELEMETRY = ROOT / "data" / "telemetry"
OUT = ROOT / "data" / "adaptive_state" / "rune"
OUT.mkdir(parents=True, exist_ok=True)

def load(name):
    p = INTEL / name
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))

def main():
    trust = load("trust_index.json")
    pressure = load("symbolic_pressure.json")
    drift = load("semantic_drift_signal.json")

    # Also try to load confidence decay from telemetry for invocation counts
    conf_path = TELEMETRY / "confidence_decay.json"
    confidence = {}
    if conf_path.exists():
        confidence = json.loads(conf_path.read_text(encoding="utf-8"))

    all_runes = set(trust) | set(pressure) | set(drift) | set(confidence)

    for rune_id in sorted(all_runes):
        t_data = trust.get(rune_id, {})
        p_data = pressure.get(rune_id, {})
        d_data = drift.get(rune_id, {})
        c_data = confidence.get(rune_id, {})

        t = t_data.get("trust_index")
        p = p_data.get("pressure_score")
        d = bool(d_data.get("drift_flag", False))

        # Get invocation count from multiple sources
        invocations = (
            c_data.get("invocations") or
            t_data.get("confidence_detail", {}).get("invocations") or
            0
        )

        # Determine lifecycle phase
        if d:
            lifecycle_phase = "volatile"
        elif isinstance(t, (int, float)) and t > 0.75:
            lifecycle_phase = "stable"
        elif isinstance(t, (int, float)) and t < 0.3:
            lifecycle_phase = "decaying"
        else:
            lifecycle_phase = "ascendant"

        # Determine stability trend
        if d:
            stability_trend = "decreasing"
        elif isinstance(t, (int, float)) and t > 0.75:
            stability_trend = "stable"
        else:
            stability_trend = "unknown"

        # Determine confidence trend
        if isinstance(t, (int, float)):
            if t < 0.5:
                confidence_trend = "decreasing"
            elif t > 0.75:
                confidence_trend = "stable"
            else:
                confidence_trend = "volatile"
        else:
            confidence_trend = "unknown"

        # Determine pressure trend
        if isinstance(p, (int, float)):
            if p > 0.7:
                pressure_trend = "high"
            elif p > 0.4:
                pressure_trend = "rising"
            else:
                pressure_trend = "low"
        else:
            pressure_trend = "unknown"

        capsule = {
            "component_id": rune_id,
            "component_type": "rune",
            "lifecycle_phase": lifecycle_phase,
            "age_cycles": invocations,
            "exposure_events": invocations,
            "cross_subsystem_interactions": {
                "telemetry": 1,
                "intel": 1,
                "memetic_weather": 1
            },
            "stability_trend": stability_trend,
            "confidence_trend": confidence_trend,
            "pressure_trend": pressure_trend,
            "notes": "",
            "last_updated_ts": datetime.now(timezone.utc).isoformat()
        }

        (OUT / f"{rune_id}.json").write_text(
            json.dumps(capsule, indent=2, sort_keys=True),
            encoding="utf-8"
        )

    print(f"✓ Adaptive State Capsules written to {OUT}")
    print(f"✓ {len(all_runes)} capsule(s) generated")

if __name__ == "__main__":
    main()
