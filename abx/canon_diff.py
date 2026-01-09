from __future__ import annotations

import argparse

# build_canon_diff replaced by evolve.canon_diff.build capability
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext


def main() -> int:
    p = argparse.ArgumentParser(
        description="Abraxas Canon Diff v0.1 (latest canon vs candidate)"
    )
    p.add_argument("--run-id", required=True)
    p.add_argument("--candidate-policy", required=True)
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument(
        "--canon-snapshot",
        default=None,
        help="Optional override; else uses latest in out/canon_snapshots",
    )
    p.add_argument("--epp", default=None)
    p.add_argument("--evogate", default=None)
    p.add_argument("--rim", default=None)
    p.add_argument("--value-ledger", default="out/value_ledgers/canon_diff_runs.jsonl")
    args = p.parse_args()

    # Create context for capability invocations
    ctx = RuneInvocationContext(
        run_id=args.run_id,
        subsystem_id="abx.canon_diff",
        git_hash="unknown"
    )

    # Build canon diff via capability contract
    canon_diff_result = invoke_capability(
        "evolve.canon_diff.build",
        {
            "run_id": args.run_id,
            "out_reports_dir": args.out_reports,
            "candidate_policy_path": args.candidate_policy,
            "epp_path": args.epp,
            "evogate_path": args.evogate,
            "rim_manifest_path": args.rim,
            "canon_snapshot_path": args.canon_snapshot
        },
        ctx=ctx,
        strict_execution=True
    )
    json_path = canon_diff_result["json_path"]
    md_path = canon_diff_result["md_path"]
    meta = canon_diff_result["meta"]

    # Append to value ledger via capability contract
    invoke_capability(
        capability="evolve.ledger.append",
        inputs={
            "ledger_path": args.value_ledger,
            "record": {"run_id": args.run_id, "canon_diff_json": json_path, "meta": meta}
        },
        ctx=ctx,
        strict_execution=True
    )
    print(f"[CANON_DIFF] wrote: {json_path}")
    print(f"[CANON_DIFF] wrote: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
