"""
Abraxas Runtime Dozen-Run Gate (artifact-level).

Usage:
  python -m scripts.dozen_run_gate_runtime --artifacts_dir ./artifacts

Replace the pipeline fns with your real Abraxas functions when wiring into your engine.
"""

import argparse

from abraxas.runtime.invariance_gate import dozen_run_tick_invariance_gate
from abraxas.runtime.tick import abraxas_tick


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifacts_dir", required=True)
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
        runs=12,
        run_once=run_once,
    )

    if not res.ok:
        print("DOZEN-RUN GATE: FAIL")
        print("expected_sha256:", res.expected_sha256)
        print("sha256s:", res.sha256s)
        print("first_mismatch_run:", res.first_mismatch_run)
        print("divergence:", res.divergence)
        return 1

    print("DOZEN-RUN GATE: PASS")
    print("sha256:", res.expected_sha256)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
