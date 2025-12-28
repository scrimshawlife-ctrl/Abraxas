#!/usr/bin/env python3
"""
Run Adaptive State Pipeline - one-shot orchestrator.

Executes the complete ASC pipeline:
  1. Build intelligence artifacts (telemetry → intel)
  2. Generate adaptive state capsules (intel + runtime events → capsules)
  3. Build aggregate index (capsules → index.json)

This ensures ASC stays fresh and grounded in actual runtime history.
"""

import subprocess
import sys

STEPS = [
    ["python3", "tools/run_intel_bridge.py"],
    ["python3", "tools/build_adaptive_state_capsules.py"],
    ["python3", "tools/build_adaptive_state_index.py"]
]

def main():
    print("=== Adaptive State Pipeline ===")
    for i, cmd in enumerate(STEPS, 1):
        print(f"\n[{i}/{len(STEPS)}] Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            print(f"✗ Step {i} failed with exit code {result.returncode}")
            sys.exit(result.returncode)
    print("\n✓ Adaptive State Pipeline complete")

if __name__ == "__main__":
    main()
