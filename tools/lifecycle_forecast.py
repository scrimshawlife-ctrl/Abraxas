#!/usr/bin/env python3
"""
Lifecycle Forecasting - predict component phase transitions deterministically.

Uses only existing artifacts (ASC + intel + runtime events) to compute:
  - Exposure velocity (recent activity vs historical)
  - Trust slope proxy (trust index vs band)
  - Stress proxy (pressure + drift)

Outputs transition probabilities + trigger conditions (rule-based, not ML).

Forecast Model (Deterministic):
  - ascendant → stable (requires: decent trust, low stress, activity)
  - stable → decaying (risk: high stress + trust decline + low velocity)
  - volatile → stable (requires: stress drop + trust recovery)
  - volatile → decaying (risk: sustained high stress + low trust)
  - decaying → fossil (requires: inactivity + age)
  - decaying → stable (recovery: trust + velocity + low stress)
  - fossil → ascendant (reawakening: significant velocity)
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict, deque

ROOT = Path(".")
ASC_DIR = ROOT / "data" / "adaptive_state" / "rune"
INTEL_DIR = ROOT / "data" / "intel"
LEDGER = ROOT / "data" / "runtime_events.log"
OUT = ROOT / "data" / "adaptive_state" / "lifecycle_forecast.json"

NOW = datetime.now(timezone.utc)

def load_json(p: Path):
    """Load JSON file if exists, else return empty dict."""
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

def clamp01(x: float) -> float:
    """Clamp value to [0.0, 1.0]."""
    return max(0.0, min(1.0, x))

def band(x: float | None):
    """Convert score to band (low/medium/high/unknown)."""
    if not isinstance(x, (int, float)):
        return "unknown"
    if x < 0.33:
        return "low"
    if x < 0.66:
        return "medium"
    return "high"

def read_recent_exposures(max_lines=5000):
    """
    Deterministic "recent window" proxy.

    Reads last max_lines from runtime_events.log (no timestamps needed).
    Counts exposures per rune in that suffix window.

    Returns:
      - recent_exposures: dict[rune_id, count]
      - window_lines: int (lines in window)
    """
    recent = defaultdict(int)
    if not LEDGER.exists():
        return recent, 0

    # Read tail safely using deque
    lines = deque(maxlen=max_lines)
    with LEDGER.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(line)

    for line in lines:
        try:
            ev = json.loads(line)
        except Exception:
            continue
        rid = ev.get("rune_id")
        ph = ev.get("phase")
        if rid and ph in ("invoke_end", "invoke_error", "reject"):
            recent[rid] += 1

    return recent, len(lines)

def phase_transition_probs(phase: str,
                           trust_index: float | None,
                           pressure_score: float | None,
                           drift_flag: bool,
                           exposure_events: int,
                           recent_exposure: int):
    """
    Deterministic heuristic for phase transition probabilities.

    Computes:
      - Exposure velocity: recent / (1 + historical average chunk)
      - Stress: pressure + drift penalty
      - Trust risk: 1 - trust

    Returns:
      - probs: dict[transition_name, probability]
      - drivers: dict with computed signals
    """
    t = trust_index if isinstance(trust_index, (int, float)) else None
    p = pressure_score if isinstance(pressure_score, (int, float)) else 0.0

    # Exposure velocity proxy: recent / (1 + historical average chunk)
    # We don't know time, so treat exposure_events as "history mass"
    vel = recent_exposure / max(1.0, (exposure_events / 10.0) if exposure_events > 0 else 1.0)
    vel = clamp01(vel)  # Keep in [0,1] as a proxy

    # Stress combines pressure + drift
    stress = clamp01(p + (0.3 if drift_flag else 0.0))

    # Trust risk is 1 - trust
    trust_risk = None if t is None else clamp01(1.0 - t)

    drivers = {
        "trust_index": t,
        "trust_band": band(t),
        "pressure_score": round(p, 4),
        "drift_flag": drift_flag,
        "stress": round(stress, 4),
        "exposure_events": exposure_events,
        "recent_exposure_window": recent_exposure,
        "velocity_proxy": round(vel, 4)
    }

    probs = {}

    if phase in ("emergent", "ascendant"):
        # Moving to stable needs: decent trust, low stress, some velocity
        base = 0.35
        if t is not None:
            base += (t - 0.5) * 0.6  # Trust helps
        base += (vel - 0.3) * 0.4  # Activity helps
        base -= stress * 0.6       # Stress hurts
        probs["ascendant_to_stable"] = round(clamp01(base), 4)

    if phase == "stable":
        # Decaying risk increases with stress + trust_risk and low velocity
        base = 0.15
        if trust_risk is not None:
            base += trust_risk * 0.7
        base += stress * 0.6
        base += (0.3 - vel) * 0.4
        probs["stable_to_decaying"] = round(clamp01(base), 4)

    if phase == "volatile":
        # Volatile stabilizes when stress is dropping and trust is decent
        base = 0.25
        if t is not None:
            base += (t - 0.4) * 0.5
        base -= stress * 0.7
        probs["volatile_to_stable"] = round(clamp01(base), 4)

        # Volatile can also decay if stress high + trust low
        base2 = 0.25 + stress * 0.6 + (trust_risk or 0.5) * 0.4
        probs["volatile_to_decaying"] = round(clamp01(base2), 4)

    if phase == "decaying":
        # Fossilization is mostly inactivity + age
        base = 0.2
        base += (0.25 - vel) * 0.6
        base += 0.2 if exposure_events > 50 else 0.0
        probs["decaying_to_fossil"] = round(clamp01(base), 4)

        # Recovery is possible: if trust decent and stress low and velocity rising
        base2 = 0.15
        if t is not None:
            base2 += (t - 0.5) * 0.6
        base2 += (vel - 0.3) * 0.5
        base2 -= stress * 0.6
        probs["decaying_to_stable"] = round(clamp01(base2), 4)

    if phase == "fossil":
        # Fossils can reawaken only with meaningful velocity
        base = 0.05 + vel * 0.6
        probs["fossil_to_ascendant"] = round(clamp01(base), 4)

    return probs, drivers

def main():
    trust = load_json(INTEL_DIR / "trust_index.json")
    pressure = load_json(INTEL_DIR / "symbolic_pressure.json")
    drift = load_json(INTEL_DIR / "semantic_drift_signal.json")

    recent, window_lines = read_recent_exposures(max_lines=5000)

    out = {
        "generated_utc": NOW.isoformat(),
        "recent_window_lines": window_lines,
        "items": []
    }

    if not ASC_DIR.exists():
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
        print(f"✓ Lifecycle forecast written to {OUT}")
        print(f"✓ 0 component(s) forecasted (no ASC data)")
        return

    for pth in sorted(ASC_DIR.glob("*.json")):
        asc = load_json(pth)
        rid = asc.get("component_id")
        if not rid:
            continue

        phase = asc.get("lifecycle_phase", "unknown")
        exposure_events = int(asc.get("exposure_events", 0) or 0)

        t = (trust.get(rid) or {}).get("trust_index")
        pr = (pressure.get(rid) or {}).get("pressure_score")
        df = bool((drift.get(rid) or {}).get("drift_flag", False))

        probs, drivers = phase_transition_probs(
            phase=phase,
            trust_index=t,
            pressure_score=pr,
            drift_flag=df,
            exposure_events=exposure_events,
            recent_exposure=int(recent.get(rid, 0))
        )

        # Triggers = explicit rule snippets (human-readable, deterministic)
        triggers = []
        if df and isinstance(t, (int, float)) and t < 0.6:
            triggers.append("drift_flag && trust_index < 0.6")
        if isinstance(pr, (int, float)) and pr >= 0.8:
            triggers.append("pressure_score >= 0.8")
        if recent.get(rid, 0) == 0 and exposure_events > 50:
            triggers.append("recent_exposure == 0 && exposure_events > 50")

        out["items"].append({
            "component_id": rid,
            "component_type": "rune",
            "current_phase": phase,
            "transition_probabilities": probs,
            "drivers": drivers,
            "triggers": triggers
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")

    print(f"✓ Lifecycle forecast written to {OUT}")
    print(f"✓ {len(out['items'])} component(s) forecasted")

if __name__ == "__main__":
    main()
