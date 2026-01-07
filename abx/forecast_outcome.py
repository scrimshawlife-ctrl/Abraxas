from __future__ import annotations

import argparse
import json

from abraxas.runes.ctx import RuneInvocationContext
from abraxas.runes.invoke import invoke_capability


def main() -> int:
    p = argparse.ArgumentParser(description="Forecast Outcome v0.1 (append outcomes to ledger)")
    p.add_argument("--run-id", required=True)
    p.add_argument("--pred-id", required=True)
    p.add_argument("--result", required=True, choices=["hit", "miss", "partial"])
    p.add_argument("--notes", default="")
    p.add_argument("--evidence-json", default=None, help="Optional JSON file containing evidence list")
    p.add_argument("--out-ledger", default="out/forecast_ledger/outcomes.jsonl")
    args = p.parse_args()

    evidence = []
    if args.evidence_json:
        with open(args.evidence_json, "r", encoding="utf-8") as f:
            evidence = json.load(f)
        if not isinstance(evidence, list):
            evidence = []

    ctx = RuneInvocationContext(
        run_id=args.run_id,
        subsystem_id="abx.forecast_outcome",
        git_hash="unknown",
    )
    invoke_capability(
        "forecast.outcome.record",
        {
            "pred_id": args.pred_id,
            "result": args.result,
            "run_id": args.run_id,
            "evidence": evidence,
            "notes": args.notes,
            "ledger_path": args.out_ledger,
        },
        ctx=ctx,
        strict_execution=True,
    )
    print(f"[FORECAST_OUTCOME] appended outcome for {args.pred_id} → {args.out_ledger}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
