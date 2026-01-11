from __future__ import annotations

import argparse

# build_dap replaced by acquire.dap.build capability
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext


def main() -> int:
    parser = argparse.ArgumentParser(description="Abraxas DAP v0.1 (Data Acquisition Planner)")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--out-dir", default="out/reports")
    parser.add_argument("--playbook", default="data/acquire/acquisition_playbook_v0_1.yaml")
    parser.add_argument("--forecast-scores", default=None)
    parser.add_argument("--regime-scores", default=None)
    parser.add_argument("--component-scores", default=None)
    parser.add_argument("--drift-report", default=None)
    parser.add_argument("--smv-report", default=None)
    parser.add_argument("--integrity-snapshot", default=None)
    args = parser.parse_args()

    # Create context for capability invocation
    ctx = RuneInvocationContext(
        run_id=args.run_id,
        subsystem_id="abx.dap",
        git_hash="unknown"
    )

    # Build DAP via capability contract
    dap_result = invoke_capability(
        "acquire.dap.build",
        {
            "run_id": args.run_id,
            "out_dir": args.out_dir,
            "playbook_path": args.playbook,
            "forecast_scores_path": args.forecast_scores,
            "regime_scores_path": args.regime_scores,
            "component_scores_path": args.component_scores,
            "drift_report_path": args.drift_report,
            "smv_report_path": args.smv_report,
            "integrity_snapshot_path": args.integrity_snapshot
        },
        ctx=ctx,
        strict_execution=True
    )
    json_path = dap_result["json_path"]
    md_path = dap_result["md_path"]

    print(f"[DAP] wrote: {json_path}")
    print(f"[DAP] wrote: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
