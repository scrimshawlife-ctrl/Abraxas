"""Memetic Weather Augment Runner — full pipeline orchestrator.

Runs the complete pipeline from runtime events to memetic weather signals:
1. Intelligence bridge (telemetry → intelligence)
2. Weather augment (intelligence → memetic weather)

Single command for end-to-end system weather generation.
"""

from __future__ import annotations

import subprocess
import sys


# Pipeline steps in dependency order
STEPS = [
    # Phase 1: Intelligence bridge (regenerate all telemetry + intelligence)
    ["python3", "tools/run_intel_bridge.py"],

    # Phase 2: Weather augment (intelligence → memetic weather)
    ["python3", "-m", "abraxas.memetic.weather_telemetry"],
]


def main() -> int:
    """Run the complete memetic weather augment pipeline."""
    print("=== Memetic Weather Augment Pipeline ===\n")

    failed = []
    succeeded = []

    for i, cmd in enumerate(STEPS, 1):
        step_name = "intelligence_bridge" if i == 1 else "weather_augment"
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
                print(f"  ✓ {step_name} completed")
                # Print key output lines
                if result.stdout:
                    lines = [l for l in result.stdout.strip().split("\n") if l]
                    for line in lines[-3:]:  # Last 3 lines
                        print(f"    {line}")
            else:
                failed.append(step_name)
                print(f"  ✗ Failed (exit code {result.returncode})")
                if result.stderr:
                    print(f"  Error: {result.stderr[:300]}")

        except Exception as e:
            failed.append(step_name)
            print(f"  ✗ Exception: {str(e)[:300]}")

        print()

    # Summary
    print("=== Pipeline Summary ===")
    print(f"Succeeded: {len(succeeded)}/{len(STEPS)}")
    print(f"Failed: {len(failed)}/{len(STEPS)}")

    if failed:
        print(f"\nFailed steps: {', '.join(failed)}")
        return 1

    print("\n✓ Memetic weather augment pipeline complete")
    print("  Artifacts:")
    print("    - data/telemetry/ (raw metrics)")
    print("    - data/intel/ (symbolic intelligence)")
    print("    - data/memetic_weather/ (weather signals)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
