#!/usr/bin/env python3
"""
Build Slang Provenance Bundles - convert slang outputs to evidence-grade artifacts.

Provenance Bundle Schema (inline, embedded):
{
  "term": str,                          # Slang term
  "weighted_score": float,              # Trust/pressure/drift/maturity adjusted score
  "confidence_band": str,               # "low" | "medium" | "high" | "unknown"
  "lifecycle_phase": str,               # From ASC: emergent | ascendant | stable | volatile | decaying | fossil
  "predicted_half_life_days": int,      # Deterministic heuristic forecast
  "weight_rationale": {
    "trust_index": float | null,
    "pressure_score": float | null,
    "drift_flag": bool,
    "maturity_adjustment": str          # Lifecycle phase influence
  },
  "evidence": {
    "intel": list[str],                 # Intel artifact filenames
    "telemetry": list[str],             # Telemetry artifact filenames
    "memetic_weather": list[str]        # Weather artifact filenames
  },
  "resonance_domains": {                # Cross-domain applicability (deterministic proxy)
    "tech": float,
    "culture": float,
    "finance": float,
    "politics": float
  },
  "epistemic_status": str,              # "emerging" | "established"
  "fragility": float                    # Instability index [0.0, 1.0]
}

Makes slang outputs hard to counterfeit - requires runtime exhaust, adaptive state, weighting logic.
"""

import json
from pathlib import Path

ROOT = Path(".")
SLANG = ROOT / "data" / "slang"
INTEL = ROOT / "data" / "intel"
ASC = ROOT / "data" / "adaptive_state" / "rune"
OUT = SLANG / "provenance_bundles.json"
SLANG.mkdir(parents=True, exist_ok=True)

def load(p):
    """Load JSON file if exists, else return empty dict."""
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

def band(x):
    """Convert score to confidence band."""
    if x is None:
        return "unknown"
    if x < 0.33:
        return "low"
    if x < 0.66:
        return "medium"
    return "high"

def predicted_half_life_days(weight, phase):
    """
    Deterministic heuristic: stronger + ascendant/stable lasts longer.

    Base formula: 30 * (1 + weight)
    Phase multipliers:
      - ascendant: 1.5x (growing)
      - stable: 1.2x (established)
      - volatile: 0.7x (unstable)

    Bounded: [7, 180] days
    """
    base = 30 * (1 + weight)
    if phase == "ascendant":
        base *= 1.5
    elif phase == "stable":
        base *= 1.2
    elif phase == "volatile":
        base *= 0.7
    return int(max(7, min(180, base)))

def compute_fragility(trust, pressure, drift_flag):
    """
    Fragility = instability index.

    Formula: (1 - trust) + pressure + (0.2 if drift else 0)
    Bounded: [0.0, 1.0]

    High fragility = likely to decay/change quickly.
    """
    t = trust if isinstance(trust, (int, float)) else 0.5
    p = pressure if isinstance(pressure, (int, float)) else 0.0
    d_penalty = 0.2 if drift_flag else 0.0
    return round(min(1.0, (1 - t) + p + d_penalty), 4)

def main():
    # Load all source artifacts
    weighted = load(SLANG / "weighted_slang_candidates.json")
    trust = load(INTEL / "trust_index.json")
    pressure = load(INTEL / "symbolic_pressure.json")
    drift = load(INTEL / "semantic_drift_signal.json")

    items = weighted.get("items", [])
    bundles = []

    for it in items:
        term = it.get("term")
        rid = it.get("source_rune_id") or it.get("rune_id") or "unknown"
        w = it.get("weighted_score")

        if not term or w is None:
            continue

        # Load ASC data for lifecycle phase
        asc = load(ASC / f"{rid}.json")
        phase = asc.get("lifecycle_phase", "unknown")

        # Extract intel metrics
        t = (trust.get(rid) or {}).get("trust_index")
        p = (pressure.get(rid) or {}).get("pressure_score")
        d = bool((drift.get(rid) or {}).get("drift_flag", False))

        # Compute derived metrics
        fragility = compute_fragility(t, p, d)
        half_life = predicted_half_life_days(w, phase)

        # Deterministic resonance proxy (can be refined with actual domain analysis later)
        # For now: tech gets boost, finance gets penalty, culture tracks base score
        resonance = {
            "tech": round(min(1.0, w + 0.2), 2),
            "culture": round(w, 2),
            "finance": round(max(0.0, w - 0.3), 2),
            "politics": round(max(0.0, w - 0.1), 2)
        }

        # Determine epistemic status
        epistemic_status = "emerging" if phase in ("emergent", "ascendant") else "established"

        bundle = {
            "term": term,
            "weighted_score": w,
            "confidence_band": band(w),
            "lifecycle_phase": phase,
            "predicted_half_life_days": half_life,
            "weight_rationale": {
                "trust_index": t,
                "pressure_score": p,
                "drift_flag": d,
                "maturity_adjustment": phase
            },
            "evidence": {
                "intel": ["trust_index.json", "symbolic_pressure.json", "semantic_drift_signal.json"],
                "telemetry": ["runtime_events.log"],
                "memetic_weather": ["telemetry_augment.json"]
            },
            "resonance_domains": resonance,
            "epistemic_status": epistemic_status,
            "fragility": fragility
        }

        bundles.append(bundle)

    # Write provenance bundles
    output = {"items": bundles, "metadata": {
        "total_bundles": len(bundles),
        "note": "Provenance bundles require runtime exhaust + ASC + intel artifacts - hard to counterfeit"
    }}

    OUT.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")

    print(f"✓ Slang provenance bundles written to {OUT}")
    print(f"✓ {len(bundles)} bundle(s) generated")

if __name__ == "__main__":
    main()
