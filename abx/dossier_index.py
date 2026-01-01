from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from abraxas.economics.costing import compute_cost


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def _list(prefix: str, root: str) -> List[str]:
    return sorted([f for f in os.listdir(root) if f.startswith(prefix)])


def main() -> int:
    p = argparse.ArgumentParser(description="Generate dossier index + credit costs")
    p.add_argument("--run-id", required=True)
    p.add_argument("--out-reports", default="out/reports")
    args = p.parse_args()

    ts = _utc_now_iso()
    root = args.out_reports

    term_dossiers = _list("term_dossier_", root)
    receipts = _list("prediction_receipt_", root)

    claims = _read_json(os.path.join(root, f"claims_{args.run_id}.json"))
    term_claims = _read_json(os.path.join(root, f"term_claims_{args.run_id}.json"))

    n_sources = len((claims.get("raw_full") or {}).get("sources") or [])
    n_claims = len((claims.get("raw_full") or {}).get("items") or [])

    term_clusters = ((term_claims.get("raw_full") or {}).get("term_clusters") or {})
    n_clusters = (
        sum(len(v) for v in term_clusters.values()) if isinstance(term_clusters, dict) else 0
    )
    n_terms = len(term_clusters) if isinstance(term_clusters, dict) else 0

    n_predictions = len(receipts)

    cost = compute_cost(
        n_sources=n_sources,
        n_claims=n_claims,
        n_clusters=n_clusters,
        n_terms=n_terms,
        n_predictions=n_predictions,
    )

    out = {
        "version": "dossier_index.v0.1",
        "run_id": args.run_id,
        "ts": ts,
        "artifacts": {
            "term_dossiers": term_dossiers,
            "prediction_receipts": receipts,
        },
        "work_metrics": {
            "sources": n_sources,
            "claims": n_claims,
            "clusters": n_clusters,
            "terms": n_terms,
            "predictions": n_predictions,
        },
        "cost": cost.to_dict(),
        "policy": {
            "browse_free": True,
            "export_metered": True,
            "non_truncation": True,
        },
        "provenance": {"builder": "abx.dossier_index.v0.1"},
    }

    path = os.path.join(root, f"dossier_index_{args.run_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"[DOSSIER_INDEX] wrote: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
