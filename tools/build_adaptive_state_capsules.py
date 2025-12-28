#!/usr/bin/env python3
"""
Build Adaptive State Capsules from telemetry and intelligence artifacts.

Offline, deterministic generator that produces per-component state capsules
recording experiential history without mutating runtime behavior.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

ROOT = Path(".")
INTEL = ROOT / "data" / "intel"
TELEMETRY = ROOT / "data" / "telemetry"
LEDGER = ROOT / "data" / "runtime_events.log"
OUT = ROOT / "data" / "adaptive_state" / "rune"
OUT.mkdir(parents=True, exist_ok=True)

def load(name):
    p = INTEL / name
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))

def count_exposures():
    """
    Deterministic scan of runtime_events.log.
    exposure_events = invoke_end + invoke_error + reject
    age_cycles = invoke_end + invoke_error (actual attempted execution)
    """
    exposure = defaultdict(int)
    cycles = defaultdict(int)
    if not LEDGER.exists():
        return exposure, cycles
    with LEDGER.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            rid = ev.get("rune_id")
            ph = ev.get("phase")
            if not rid or not ph:
                continue
            if ph in ("invoke_end", "invoke_error", "reject"):
                exposure[rid] += 1
            if ph in ("invoke_end", "invoke_error"):
                cycles[rid] += 1
    return exposure, cycles

def subsystem_touches():
    """
    Compute cross-subsystem interactions from artifact presence.
    Deterministic check: if directory exists and has files, count = 1.
    """
    touches = {
        "telemetry": (ROOT / "data" / "telemetry").exists(),
        "intel": (ROOT / "data" / "intel").exists(),
        "memetic_weather": (ROOT / "data" / "memetic_weather").exists(),
        "slang": (ROOT / "data" / "slang").exists()
    }
    return {k: (1 if v else 0) for k, v in touches.items()}

def main():
    trust = load("trust_index.json")
    pressure = load("symbolic_pressure.json")
    drift = load("semantic_drift_signal.json")

    # Real counts from runtime events (deterministic)
    exposure, cycles = count_exposures()

    # Cross-subsystem touches from artifact presence
    touches = subsystem_touches()

    # Combine all known runes from all sources
    all_runes = set(trust) | set(pressure) | set(drift) | set(exposure)

    for rune_id in sorted(all_runes):
        t_data = trust.get(rune_id, {})
        p_data = pressure.get(rune_id, {})
        d_data = drift.get(rune_id, {})

        t = t_data.get("trust_index")
        p = p_data.get("pressure_score")
        d = bool(d_data.get("drift_flag", False))

        # Real counts from runtime events (grounded in actual history)
        age_cycles_count = int(cycles.get(rune_id, 0))
        exposure_events_count = int(exposure.get(rune_id, 0))

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
            "age_cycles": age_cycles_count,
            "exposure_events": exposure_events_count,
            "cross_subsystem_interactions": touches,
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
