#!/usr/bin/env python3
"""
Build Adaptive State Index - aggregate capsule summary for fast consumption.

Reads all capsule files and emits a single index.json with key metrics
from each component, optimized for quick ingestion by downstream consumers.
"""

import json
from pathlib import Path

ROOT = Path(".")
ASC_DIR = ROOT / "data" / "adaptive_state" / "rune"
OUT = ROOT / "data" / "adaptive_state"
OUT.mkdir(parents=True, exist_ok=True)

def main():
    index = {"components": []}
    if not ASC_DIR.exists():
        (OUT / "index.json").write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")
        print(f"✓ Empty index written to {OUT / 'index.json'}")
        return

    for p in sorted(ASC_DIR.glob("*.json")):
        try:
            c = json.loads(p.read_text(encoding="utf-8"))
            index["components"].append({
                "component_id": c.get("component_id"),
                "type": c.get("component_type"),
                "phase": c.get("lifecycle_phase"),
                "age_cycles": c.get("age_cycles"),
                "exposure_events": c.get("exposure_events"),
                "stability_trend": c.get("stability_trend"),
                "confidence_trend": c.get("confidence_trend"),
                "pressure_trend": c.get("pressure_trend"),
                "last_updated_ts": c.get("last_updated_ts")
            })
        except Exception:
            continue

    (OUT / "index.json").write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")
    print(f"✓ Adaptive State Index written to {OUT / 'index.json'}")
    print(f"✓ {len(index['components'])} component(s) indexed")

if __name__ == "__main__":
    main()
