"""Failure Cluster Interpreter — identify unstable runes and error patterns.

Reads runtime_events.log and groups failures by rune and error type.
Enables targeted debugging and stability risk assessment.
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
    """Generate failure clustering analysis from runtime events."""
    OUT.mkdir(parents=True, exist_ok=True)

    # Collect failures by rune and error type
    fails: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    total_errors = 0

    for ev in iter_events():
        if ev.get("phase") == "invoke_error":
            rid = ev.get("rune_id")
            et = ev.get("error_type", "Unknown")
            fails[rid][et] += 1
            total_errors += 1

    # Sort error types by frequency within each rune
    summary: dict[str, dict[str, int]] = {}
    for rid, errmap in fails.items():
        summary[rid] = dict(sorted(errmap.items(), key=lambda x: -x[1]))

    # Write output
    path = OUT / "failure_clusters.json"
    path.write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"Failure clusters written to: {path}")
    print(f"Analyzed {total_errors} errors across {len(summary)} runes")

    # Print summary to console
    if summary:
        print("\nTop failure patterns:")
        for rid in sorted(summary.keys()):
            errors = summary[rid]
            total_for_rune = sum(errors.values())
            print(f"  {rid}: {total_for_rune} errors")
            for error_type, count in list(errors.items())[:3]:
                print(f"    - {error_type}: {count}")


if __name__ == "__main__":
    main()
