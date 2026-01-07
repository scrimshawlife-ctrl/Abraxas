from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any

from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext
# memetic functions wired through capabilities


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main() -> int:
    p = argparse.ArgumentParser(description="Claims clustering run (consensus gap)")
    p.add_argument("--run-id", required=True)
    p.add_argument("--osh-ledger", default="out/osh_ledgers/fetch_artifacts.jsonl")
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument("--sim-threshold", type=float, default=0.42)
    p.add_argument("--max-pairs", type=int, default=250000)
    p.add_argument("--max-per-source", type=int, default=5)
    args = p.parse_args()

    ts = _utc_now_iso()
    # Create context for capability invocations
    ctx = RuneInvocationContext(
        run_id=args.run_id,
        subsystem_id="abx.claims_run",
        git_hash="unknown"
    )
    sources_result = invoke_capability(
        "memetic.claims_sources.load",
        {"osh_ledger_path": args.osh_ledger},
        ctx=ctx,
        strict_execution=True
    )
    sources, sig = sources_result["sources"], sources_result["stats"]
    items_result = invoke_capability(
        "memetic.claim_extract.items",
        {
            "sources": sources,
            "run_id": args.run_id,
            "max_per_source": int(args.max_per_source),
        },
        ctx=ctx,
        strict_execution=True,
    )
    items = items_result["items"]
    clusters_result = invoke_capability(
        "memetic.claim_cluster.cluster",
        {
            "items": items,
            "sim_threshold": float(args.sim_threshold),
            "max_pairs": int(args.max_pairs),
        },
        ctx=ctx,
        strict_execution=True,
    )
    clusters = clusters_result["clusters"]
    metrics = clusters_result["metrics"]

    top_clusters = []
    for cluster in clusters[:8]:
        rep = items[cluster[0]].get("claim") if cluster else ""
        domains = sorted({items[i].get("domain") for i in cluster if items[i].get("domain")})
        top_clusters.append({"n": len(cluster), "rep": rep, "domains": domains[:10]})

    core = {
        "version": "claims.v0.1",
        "run_id": args.run_id,
        "ts": ts,
        "metrics": metrics,
        "views": {"top_clusters": top_clusters},
        "provenance": {
            "builder": "abx.claims_run.v0.1",
            "osh_ledger": args.osh_ledger,
            "sim_threshold": args.sim_threshold,
            "max_pairs": args.max_pairs,
        },
    }

    # Enforce non-truncation policy via capability contract
    ctx = RuneInvocationContext(
        run_id=args.run_id,
        subsystem_id="abx.claims_run",
        git_hash="unknown"
    )
    result = invoke_capability(
        capability="evolve.policy.enforce_non_truncation",
        inputs={
            "artifact": core,
            "raw_full": {"sources": sources, "signals": sig, "items": items, "clusters": clusters}
        },
        ctx=ctx,
        strict_execution=True
    )
    out = result["artifact"]

    path = os.path.join(args.out_reports, f"claims_{args.run_id}.json")
    _write_json(path, out)
    print(f"[CLAIMS_RUN] wrote: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
