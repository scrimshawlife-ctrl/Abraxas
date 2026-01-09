from __future__ import annotations

import argparse
import json
import os

# build_evogate replaced by evolve.evogate.build capability
# build_rim_from_osh_ledger replaced by evolve.rim.build_from_osh_ledger capability
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext


def main() -> int:
    p = argparse.ArgumentParser(
        description="Abraxas EvoGate v0.1 (staging apply + replay gate)"
    )
    p.add_argument("--run-id", required=True)
    p.add_argument("--epp", required=True, help="Path to out/reports/epp_<run_id>.json")
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument("--staging-root", default="out/staging")
    p.add_argument("--base-policy", default=None, help="Optional base policy JSON")
    p.add_argument("--baseline-metrics", default=None, help="Optional baseline metrics JSON")
    p.add_argument(
        "--replay-inputs-dir",
        default=None,
        help="Optional inputs dir passed to replay command",
    )
    p.add_argument(
        "--build-rim-from-osh-ledger",
        default=None,
        help="If set, build replay_inputs manifest from this OSH ledger and use it.",
    )
    p.add_argument(
        "--replay-cmd",
        default=None,
        help="Optional override for ABRAXAS_REPLAY_CMD",
    )
    p.add_argument("--thresholds", default=None, help="Optional thresholds JSON string or path")
    p.add_argument("--value-ledger", default="out/value_ledgers/evogate_runs.jsonl")
    args = p.parse_args()

    thresholds = None
    if args.thresholds:
        if args.thresholds.strip().startswith("{"):
            thresholds = json.loads(args.thresholds)
        else:
            with open(args.thresholds, "r", encoding="utf-8") as f:
                thresholds = json.load(f)

    # Create context for capability invocations
    ctx = RuneInvocationContext(
        run_id=args.run_id,
        subsystem_id="abx.evogate",
        git_hash="unknown"
    )

    replay_inputs_dir = args.replay_inputs_dir
    if args.build_rim_from_osh_ledger:
        rim_result = invoke_capability(
            "evolve.rim.build_from_osh_ledger",
            {
                "run_id": args.run_id,
                "out_root": "out/replay_inputs",
                "osh_ledger_path": args.build_rim_from_osh_ledger
            },
            ctx=ctx,
            strict_execution=True
        )
        rim_path = rim_result["rim_path"]
        replay_inputs_dir = os.path.dirname(rim_path)

    evogate_result = invoke_capability(
        "evolve.evogate.build",
        {
            "run_id": args.run_id,
            "out_reports_dir": args.out_reports,
            "staging_root_dir": args.staging_root,
            "epp_path": args.epp,
            "base_policy_path": args.base_policy,
            "baseline_metrics_path": args.baseline_metrics,
            "replay_inputs_dir": replay_inputs_dir,
            "replay_cmd": args.replay_cmd,
            "thresholds": thresholds
        },
        ctx=ctx,
        strict_execution=True
    )
    json_path = evogate_result["json_path"]
    md_path = evogate_result["md_path"]
    meta = evogate_result["meta"]

    # Append to value ledger via capability contract
    invoke_capability(
        capability="evolve.ledger.append",
        inputs={
            "ledger_path": args.value_ledger,
            "record": {"run_id": args.run_id, "evogate_json": json_path, "meta": meta}
        },
        ctx=ctx,
        strict_execution=True
    )
    print(f"[EVOGATE] wrote: {json_path}")
    print(f"[EVOGATE] wrote: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
