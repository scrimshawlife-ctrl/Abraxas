"""Intelligence Bridge Runner — orchestrates telemetry → intelligence pipeline.

Runs the complete analysis pipeline:
1. Telemetry interpreters (latency, failures, drift, confidence)
2. Intelligence derivers (pressure, drift signal, trust)

Can be run manually, via cron, or triggered from CI. No runtime coupling.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


# Analysis pipeline in dependency order
STEPS = [
    # Phase 1: Telemetry interpreters (read runtime_events.log)
    ["python3", "tools/telemetry_latency.py"],
    ["python3", "tools/telemetry_failures.py"],
    ["python3", "tools/telemetry_drift.py"],
    ["python3", "tools/telemetry_confidence.py"],

    # Phase 2: Intelligence derivers (read telemetry, emit intelligence)
    ["python3", "tools/intel_pressure.py"],
    ["python3", "tools/intel_drift_signal.py"],
    ["python3", "tools/intel_trust_index.py"],
]


def main() -> int:
    """Run the complete intelligence bridge pipeline."""
    print("=== Intelligence Bridge Pipeline ===\n")

    failed = []
    succeeded = []

    for i, cmd in enumerate(STEPS, 1):
        step_name = Path(cmd[1]).stem
        print(f"[{i}/{len(STEPS)}] Running {step_name}...")

        try:
            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                succeeded.append(step_name)
                # Print last line of output (usually the artifact path)
                if result.stdout:
                    last_line = result.stdout.strip().split("\n")[-1]
                    print(f"  ✓ {last_line}")
            else:
                failed.append(step_name)
                print(f"  ✗ Failed (exit code {result.returncode})")
                if result.stderr:
                    print(f"  Error: {result.stderr[:200]}")

        except Exception as e:
            failed.append(step_name)
            print(f"  ✗ Exception: {str(e)[:200]}")

        print()

    # Summary
    print("=== Pipeline Summary ===")
    print(f"Succeeded: {len(succeeded)}/{len(STEPS)}")
    print(f"Failed: {len(failed)}/{len(STEPS)}")

    if failed:
        print(f"\nFailed steps: {', '.join(failed)}")
        return 1

    print("\n✓ Intelligence bridge complete")
    print("  Artifacts: data/telemetry/ + data/intel/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
