"""
Abraxas Runtime Dozen-Run Gate (artifact-level).

Usage:
  python -m scripts.dozen_run_gate_runtime --artifacts_dir ./artifacts
  python -m scripts.dozen_run_gate_runtime --artifacts_dir ./artifacts --run_id my_run --runs 12

Replace the pipeline fns with your real Abraxas functions when wiring into your engine.

Gate v2 checks both:
  1. TrendPack sha256 invariance
  2. RunHeader sha256 invariance

On completion (pass or fail), writes:
  - RunStability.v0: runs/<run_id>.runstability.json
  - StabilityRef.v0: runs/<run_id>.stability_ref.json

On failure, emits field-level drift diff for debugging.
"""

import argparse

from abraxas.runtime.invariance_gate import dozen_run_tick_invariance_gate
from abraxas.runtime.run_stability import write_run_stability, write_stability_ref
from abraxas.runtime.tick import abraxas_tick


def main() -> int:
    ap = argparse.ArgumentParser(description="Run dozen-run invariance gate")
    ap.add_argument("--artifacts_dir", required=True, help="Root artifacts directory")
    ap.add_argument("--runs", type=int, default=12, help="Number of runs (default: 12)")
    ap.add_argument("--run_id", default="dozen_gate", help="Run ID for stability record")
    args = ap.parse_args()

    # NOTE: wire real pipeline callables here in your actual engine integration.
    def run_signal(ctx): return {"signal": 1}
    def run_compress(ctx): return {"compress": 1}
    def run_overlay(ctx): return {"overlay": 1}

    def run_once(i: int, artifacts_dir: str):
        return abraxas_tick(
            tick=0,
            run_id=args.run_id,
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

    # Build gate result dict for persistence
    gate_obj = {
        "ok": res.ok,
        "expected_sha256": res.expected_sha256,
        "sha256s": res.sha256s,
        "expected_runheader_sha256": res.expected_runheader_sha256,
        "runheader_sha256s": res.runheader_sha256s,
        "first_mismatch_run": res.first_mismatch_run,
        "divergence": res.divergence,
    }

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
            if res.divergence.get("kind") == "trendpack_content_mismatch":
                print("  event_index:", res.divergence.get("event_index"))
                print("  baseline_trendpack:", res.divergence.get("baseline_trendpack"))
                print("  mismatch_trendpack:", res.divergence.get("mismatch_trendpack"))
                print("  diff:", res.divergence.get("diff"))
            elif res.divergence.get("kind") == "runheader_sha256_mismatch":
                print("  baseline_runheader:", res.divergence.get("baseline_runheader"))
                print("  mismatch_runheader:", res.divergence.get("mismatch_runheader"))
                print("  diffs:", res.divergence.get("diffs"))

        # Write stability artifacts even on failure
        stability_path, stability_sha = write_run_stability(
            artifacts_dir=args.artifacts_dir,
            run_id=args.run_id,
            gate_result=gate_obj,
            note="dozen-run gate failure",
        )
        ref_path, ref_sha = write_stability_ref(
            artifacts_dir=args.artifacts_dir,
            run_id=args.run_id,
            runstability_path=stability_path,
            runstability_sha256=stability_sha,
        )
        print()
        print("Stability artifacts written:")
        print(f"  RunStability: {stability_path}")
        print(f"  StabilityRef: {ref_path}")
        return 1

    print("DOZEN-RUN GATE: PASS")
    print("=" * 60)
    print("TrendPack sha256:", res.expected_sha256)
    print("RunHeader sha256:", res.expected_runheader_sha256)
    print(f"All {len(res.sha256s)} runs produced identical artifacts.")

    # Write stability artifacts on success
    stability_path, stability_sha = write_run_stability(
        artifacts_dir=args.artifacts_dir,
        run_id=args.run_id,
        gate_result=gate_obj,
        note="dozen-run gate pass",
    )
    ref_path, ref_sha = write_stability_ref(
        artifacts_dir=args.artifacts_dir,
        run_id=args.run_id,
        runstability_path=stability_path,
        runstability_sha256=stability_sha,
    )
    print()
    print("Stability artifacts written:")
    print(f"  RunStability: {stability_path}")
    print(f"  StabilityRef: {ref_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
