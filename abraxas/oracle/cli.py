"""Deterministic CLI for daily oracle runs."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from datetime import date
from typing import List

from abraxas.core.canonical import canonical_json
from abraxas.oracle.runner import DeterministicOracleRunner, OracleConfig
from abraxas.oracle.transforms import CorrelationDelta


def _parse_date(s: str) -> date:
    """Parse ISO date string (YYYY-MM-DD)."""
    return date.fromisoformat(s)


def _load_deltas(path: str) -> List[CorrelationDelta]:
    """Load correlation deltas from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    # accepts {"deltas":[...]} or [...]
    deltas_obj = obj["deltas"] if isinstance(obj, dict) and "deltas" in obj else obj
    out: List[CorrelationDelta] = []
    for d in deltas_obj:
        out.append(
            CorrelationDelta(
                domain_a=d["domain_a"],
                domain_b=d["domain_b"],
                key=d["key"],
                delta=float(d["delta"]),
                observed_at_utc=d["observed_at_utc"],
            )
        )
    return out


def main() -> None:
    """Main CLI entry point."""
    p = argparse.ArgumentParser(prog="abraxas-oracle")
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    p.add_argument("--deltas", required=True, help="Path to correlation deltas JSON")
    p.add_argument("--half-life-hours", type=float, default=24.0)
    p.add_argument("--top-k", type=int, default=12)
    p.add_argument("--run-id", default=None)
    p.add_argument("--as-of-utc", default=None, help="ISO8601 Z (optional)")
    p.add_argument("--store", action="store_true", help="Persist to Postgres (requires DATABASE_URL)")
    args = p.parse_args()

    d = _parse_date(args.date)
    deltas = _load_deltas(args.deltas)

    runner = DeterministicOracleRunner(
        git_sha=os.getenv("GIT_SHA"),
        host=os.getenv("HOSTNAME"),
    )
    cfg = OracleConfig(half_life_hours=args.half_life_hours, top_k=args.top_k)

    art = runner.run_for_date(
        d,
        deltas,
        cfg,
        run_id=args.run_id,
        as_of_utc=args.as_of_utc,
    )

    if args.store:
        from abraxas.oracle.pg_store import PostgresOracleStore

        store = PostgresOracleStore()
        store.upsert(art)

    # deterministic print (canonical)
    print(
        canonical_json(
            {
                "id": art.id,
                "date": art.date,
                "inputs": art.inputs,
                "output": art.output,
                "signature": art.signature,
                "provenance": asdict(art.provenance),
            }
        )
    )


if __name__ == "__main__":
    main()
