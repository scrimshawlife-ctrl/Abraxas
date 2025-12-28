"""Result Shape Drift Detector — detect silent semantic instability.

Reads runtime_events.log and identifies runes with changing result structures.
Flags semantic drift even when code "still works" - prevents silent regressions.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from abx.telemetry_reader import iter_events

OUT = Path(__file__).resolve().parents[1] / "data" / "telemetry"


def main() -> None:
    """Generate result shape drift analysis from runtime events."""
    OUT.mkdir(parents=True, exist_ok=True)

    # Collect unique result shapes per rune
    shapes: dict[str, set[tuple[str, ...]]] = defaultdict(set)

    for ev in iter_events():
        if ev.get("phase") == "invoke_end":
            rid = ev.get("rune_id")
            keys = tuple(ev.get("result_keys") or [])
            if keys:
                shapes[rid].add(keys)

    # Flag runes with multiple result shapes (drift detected)
    drift: dict[str, dict[str, Any]] = {}
    for rid, variants in shapes.items():
        if len(variants) > 1:
            drift[rid] = {
                "variants": [list(v) for v in sorted(variants)],
                "variant_count": len(variants),
                "severity": "high" if len(variants) > 2 else "medium",
            }

    # Write output
    path = OUT / "result_shape_drift.json"
    path.write_text(
        json.dumps(drift, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"Result shape drift analysis written to: {path}")
    print(f"Detected drift in {len(drift)} runes")

    # Print drift summary to console
    if drift:
        print("\nRunes with result shape drift:")
        for rid in sorted(drift.keys()):
            d = drift[rid]
            print(f"  {rid}: {d['variant_count']} variants ({d['severity']} severity)")
            for i, variant in enumerate(d['variants'], 1):
                print(f"    Variant {i}: {variant}")
    else:
        print("\nNo result shape drift detected - all runes have stable outputs")


if __name__ == "__main__":
    main()
