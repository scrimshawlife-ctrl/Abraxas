#!/usr/bin/env python3
"""
Run Slang Provenance Pipeline - one-shot orchestrator for evidence-grade slang artifacts.

Executes complete pipeline:
  1. Build intelligence artifacts (telemetry → intel)
  2. Apply trust/pressure/drift/maturity weights to slang candidates
  3. Generate provenance bundles with lifecycle awareness

Output: data/slang/provenance_bundles.json
"""

import subprocess
import sys

STEPS = [
    ["python3", "tools/run_intel_bridge.py"],
    ["python3", "tools/slang_apply_weights.py"],
    ["python3", "tools/build_slang_provenance.py"]
]

def main():
    print("=== Slang Provenance Pipeline ===")
    for i, cmd in enumerate(STEPS, 1):
        print(f"\n[{i}/{len(STEPS)}] Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            print(f"✗ Step {i} failed with exit code {result.returncode}")
            sys.exit(result.returncode)
    print("\n✓ Slang provenance pipeline complete")

if __name__ == "__main__":
    main()
