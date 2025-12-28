"""Drift Signal Extractor — semantic instability detector.

Concept: Result shape drift = semantic instability, not just bugs.

Becomes input for:
- Slang emergence weighting
- Confidence decay
- Forecast reliability gating
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from abx.intel_bridge import load, emit


def main() -> None:
    """Generate semantic drift signal from telemetry."""
    drift = load("result_shape_drift.json")
    failures = load("failure_clusters.json")

    signal: dict[str, dict[str, any]] = {}

    # Extract drift signals and correlate with failures
    for rid, d in drift.items():
        fail_modes = failures.get(rid, {})

        signal[rid] = {
            "variant_count": d.get("variant_count", 0),
            "variants": d.get("variants", []),
            "failure_modes": list(fail_modes.keys()),
            "failure_count": sum(fail_modes.values()),
            "drift_flag": True,
            "severity": d.get("severity", "unknown"),
            "drift_with_failures": len(fail_modes) > 0,
        }

    # Emit intelligence artifact
    path = emit("semantic_drift_signal.json", signal)
    print(f"Semantic drift signal written to: {path}")
    print(f"Detected drift in {len(signal)} runes")

    # Console summary
    if signal:
        print("\nDrift signals:")
        for rid in sorted(signal.keys()):
            s = signal[rid]
            severity = s["severity"]
            variants = s["variant_count"]
            failures = s["failure_count"]
            print(f"  {rid}: {variants} variants ({severity}), {failures} failures")
            if s["drift_with_failures"]:
                print(f"    ⚠️  Drift correlated with failures: {s['failure_modes']}")
    else:
        print("\nNo semantic drift detected - all runes have stable outputs")


if __name__ == "__main__":
    main()
