"""Latency Baseline Interpreter — establish normal performance envelopes per rune.

Reads runtime_events.log and produces latency distribution statistics.
Enables performance regression detection without guesswork.
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from abx.telemetry_reader import iter_events

OUT = Path(__file__).resolve().parents[1] / "data" / "telemetry"


def main() -> None:
    """Generate latency baseline statistics from runtime events."""
    OUT.mkdir(parents=True, exist_ok=True)

    # Collect duration samples per rune
    durations: dict[str, list[int]] = defaultdict(list)

    for ev in iter_events():
        if ev.get("phase") == "invoke_end":
            rid = ev.get("rune_id")
            d = ev.get("duration_ns")
            if isinstance(d, int) and d > 0:
                durations[rid].append(d)

    # Compute statistics for each rune
    summary: dict[str, dict[str, int]] = {}
    for rid, vals in durations.items():
        if len(vals) < 3:
            # Need at least 3 samples for meaningful stats
            continue

        summary[rid] = {
            "count": len(vals),
            "p50_ns": int(statistics.median(vals)),
            "p95_ns": int(statistics.quantiles(vals, n=20)[18]) if len(vals) >= 20 else int(max(vals)),
            "max_ns": int(max(vals)),
            "min_ns": int(min(vals)),
            "mean_ns": int(statistics.mean(vals)),
        }

    # Write output
    path = OUT / "latency_baselines.json"
    path.write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"Latency baselines written to: {path}")
    print(f"Analyzed {len(summary)} runes with {sum(s['count'] for s in summary.values())} total invocations")


if __name__ == "__main__":
    main()
