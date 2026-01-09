from __future__ import annotations

import argparse

# build_promotion_packet replaced by evolve.promotion.build capability
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext


def main() -> int:
    p = argparse.ArgumentParser(
        description="Abraxas Promote v0.1 (human-approved promotion packet)"
    )
    p.add_argument("--run-id", required=True)
    p.add_argument("--epp", required=True)
    p.add_argument("--evogate", required=True)
    p.add_argument("--rim", required=True, help="Path to out/replay_inputs/<run_id>/manifest.json")
    p.add_argument(
        "--candidate-policy",
        required=True,
        help="Path to out/staging/<run_id>/candidate_policy.json",
    )
    p.add_argument("--out-dir", default="out/promotions")
    p.add_argument("--emit-canon-snapshot", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--value-ledger", default="out/value_ledgers/promotion_runs.jsonl")
    args = p.parse_args()

    # Create context for capability invocations
    ctx = RuneInvocationContext(
        run_id=args.run_id,
        subsystem_id="abx.promote",
        git_hash="unknown"
    )

    # Build promotion packet via capability contract
    promotion_result = invoke_capability(
        "evolve.promotion.build",
        {
            "run_id": args.run_id,
            "out_dir": args.out_dir,
            "epp_path": args.epp,
            "evogate_path": args.evogate,
            "rim_manifest_path": args.rim,
            "candidate_policy_path": args.candidate_policy,
            "emit_canon_snapshot": bool(args.emit_canon_snapshot),
            "force": bool(args.force)
        },
        ctx=ctx,
        strict_execution=True
    )
    json_path = promotion_result["json_path"]
    md_path = promotion_result["md_path"]
    canon_path = promotion_result["canon_snapshot_path"]
    meta = promotion_result["meta"]

    # Append to value ledger via capability contract
    invoke_capability(
        capability="evolve.ledger.append",
        inputs={
            "ledger_path": args.value_ledger,
            "record": {"run_id": args.run_id, "promotion_json": json_path, "meta": meta}
        },
        ctx=ctx,
        strict_execution=True
    )
    print(f"[PROMOTE] wrote: {json_path}")
    print(f"[PROMOTE] wrote: {md_path}")
    if canon_path:
        print(f"[PROMOTE] canon snapshot: {canon_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
