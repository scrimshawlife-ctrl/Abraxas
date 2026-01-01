#!/usr/bin/env python3
"""
Retirement Recommendations - deterministic heuristics for component lifecycle pruning.

Generates advisory recommendations for component retirement based on ASC metrics.
Does NOT automatically change any state - outputs suggestions only.

Recommendations are governance inputs, not automated actions.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

ASC_DIR = Path("data/adaptive_state/rune")
OUT = Path("data/adaptive_state")
OUT.mkdir(parents=True, exist_ok=True)

NOW = datetime.now(timezone.utc)

def load_json(p):
    return json.loads(p.read_text(encoding="utf-8"))

def days_since(ts):
    """Calculate days since timestamp (idle duration)."""
    try:
        t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return (NOW - t).days
    except Exception:
        return None

def main():
    recs = {"recommendations": [], "metadata": {
        "generated_at": NOW.isoformat(),
        "total_scanned": 0,
        "total_recommendations": 0
    }}

    if not ASC_DIR.exists():
        out = OUT / "retirement_recommendations.json"
        out.write_text(json.dumps(recs, indent=2, sort_keys=True), encoding="utf-8")
        print(f"✓ No ASC data found, empty recommendations written to {out}")
        return

    scanned = 0
    for p in sorted(ASC_DIR.glob("*.json")):
        scanned += 1
        c = load_json(p)
        cid = c.get("component_id")
        phase = c.get("lifecycle_phase")
        trust_trend = c.get("confidence_trend")
        pressure_trend = c.get("pressure_trend")
        stability_trend = c.get("stability_trend")
        age = c.get("age_cycles", 0)
        exposure = c.get("exposure_events", 0)
        last_ts = c.get("last_updated_ts")
        idle_days = days_since(last_ts)

        # Rule 1: Decay candidate (trust declining + pressure rising)
        if trust_trend == "decreasing" and pressure_trend in ("high", "rising"):
            recs["recommendations"].append({
                "component_id": cid,
                "current_phase": phase,
                "suggested_state": "decaying",
                "rule": "trust_decreasing && pressure_high",
                "severity": "medium",
                "evidence": {
                    "confidence_trend": trust_trend,
                    "pressure_trend": pressure_trend
                },
                "note": "Component experiencing sustained decline with rising operational pressure"
            })

        # Rule 2: Fossil candidate (aged + dormant)
        if age > 50 and idle_days is not None and idle_days > 30:
            recs["recommendations"].append({
                "component_id": cid,
                "current_phase": phase,
                "suggested_state": "fossil",
                "rule": "age_cycles>50 && idle_days>30",
                "severity": "low",
                "evidence": {
                    "age_cycles": age,
                    "exposure_events": exposure,
                    "idle_days": idle_days
                },
                "note": "Component aged and dormant - candidate for archeological preservation"
            })

        # Rule 3: Fossil candidate (already decaying + no activity)
        if phase == "decaying" and idle_days is not None and idle_days > 14:
            recs["recommendations"].append({
                "component_id": cid,
                "current_phase": phase,
                "suggested_state": "fossil",
                "rule": "phase==decaying && idle_days>14",
                "severity": "medium",
                "evidence": {
                    "lifecycle_phase": phase,
                    "idle_days": idle_days
                },
                "note": "Decaying component with no recent activity - retirement candidate"
            })

    recs["metadata"]["total_scanned"] = scanned
    recs["metadata"]["total_recommendations"] = len(recs["recommendations"])

    out = OUT / "retirement_recommendations.json"
    out.write_text(json.dumps(recs, indent=2, sort_keys=True), encoding="utf-8")

    print(f"✓ Retirement recommendations written to {out}")
    print(f"✓ Scanned {scanned} component(s), generated {len(recs['recommendations'])} recommendation(s)")

if __name__ == "__main__":
    main()
