"""
Abraxas Runtime Dozen-Run Gate (artifact-level).

Usage:
  python -m scripts.dozen_run_gate_runtime --artifacts_dir ./artifacts

Replace the pipeline fns with your real Abraxas functions when wiring into your engine.

Gate v2 checks both:
  1. TrendPack sha256 invariance
  2. RunHeader sha256 invariance

On failure, emits field-level drift diff for debugging.
"""

import argparse

from abraxas.runtime.invariance_gate import dozen_run_tick_invariance_gate
from abraxas.runtime.tick import abraxas_tick


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifacts_dir", required=True)
    ap.add_argument("--runs", type=int, default=12, help="Number of runs (default: 12)")
    args = ap.parse_args()

    # NOTE: wire real pipeline callables here in your actual engine integration.
    def run_signal(ctx): return {"signal": 1}
    def run_compress(ctx): return {"compress": 1}
    def run_overlay(ctx): return {"overlay": 1}

    def run_once(i: int, artifacts_dir: str):
        return abraxas_tick(
            tick=0,
            run_id="dozen_gate",
            mode="sandbox",
            context={"x": 1},
            artifacts_dir=artifacts_dir,
            run_signal=run_signal,
            run_compress=run_compress,
            run_overlay=run_overlay,
            run_shadow_tasks={"sei": lambda ctx: {"sei": 0}},
        )

    res = dozen_run_tick_invariance_gate(
        base_artifacts_dir=args.artifacts_dir,
        runs=args.runs,
        run_once=run_once,
    )

    if not res.ok:
        print("DOZEN-RUN GATE: FAIL")
        print("=" * 60)
        print("TrendPack:")
        print("  expected_sha256:", res.expected_sha256)
        print("  sha256s:", res.sha256s)
        print()
        print("RunHeader:")
        print("  expected_runheader_sha256:", res.expected_runheader_sha256)
        print("  runheader_sha256s:", res.runheader_sha256s)
        print()
        print("Divergence:")
        print("  first_mismatch_run:", res.first_mismatch_run)
        print("  kind:", res.divergence.get("kind") if res.divergence else None)
        if res.divergence:
            if res.divergence.get("kind") == "trendpack_sha256_mismatch":
                print("  event_index:", res.divergence.get("event_index"))
                print("  baseline_trendpack:", res.divergence.get("baseline_trendpack"))
                print("  mismatch_trendpack:", res.divergence.get("mismatch_trendpack"))
                print("  diff:", res.divergence.get("diff"))
            elif res.divergence.get("kind") == "runheader_sha256_mismatch":
                print("  baseline_runheader:", res.divergence.get("baseline_runheader"))
                print("  mismatch_runheader:", res.divergence.get("mismatch_runheader"))
                print("  diffs:", res.divergence.get("diffs"))
        return 1

    print("DOZEN-RUN GATE: PASS")
    print("=" * 60)
    print("TrendPack sha256:", res.expected_sha256)
    print("RunHeader sha256:", res.expected_runheader_sha256)
    print(f"All {len(res.sha256s)} runs produced identical artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
