from __future__ import annotations

import argparse

from abraxas.evolve.canon_diff import build_canon_diff
from abraxas.evolve.ledger import append_chained_jsonl


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

    json_path, md_path, meta = build_canon_diff(
        run_id=args.run_id,
        out_reports_dir=args.out_reports,
        candidate_policy_path=args.candidate_policy,
        epp_path=args.epp,
        evogate_path=args.evogate,
        rim_manifest_path=args.rim,
        canon_snapshot_path=args.canon_snapshot,
    )
    append_chained_jsonl(
        args.value_ledger,
        {"run_id": args.run_id, "canon_diff_json": json_path, "meta": meta},
    )
    print(f"[CANON_DIFF] wrote: {json_path}")
    print(f"[CANON_DIFF] wrote: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
