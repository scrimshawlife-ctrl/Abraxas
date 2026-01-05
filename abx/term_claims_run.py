from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from abraxas.memetic.claim_cluster import cluster_claims
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext
from abraxas.memetic.claim_extract import extract_claim_items_from_sources
from abraxas.memetic.claims_sources import load_sources_from_osh
from abraxas.memetic.term_assign import build_term_token_index, assign_claim_to_terms
from abraxas.evidence.index import evidence_by_term
from abraxas.evidence.support import support_weight_for_claim
from abraxas.conspiracy.csp import compute_claim_csp


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _load_terms_from_a2(a2_path: str, max_terms: int = 5000) -> List[str]:
    if not os.path.exists(a2_path):
        return []
    try:
        with open(a2_path, "r", encoding="utf-8") as f:
            a2 = json.load(f)
        raw = a2.get("raw_full") or {}
        profiles = None
        if isinstance(raw, dict) and isinstance(raw.get("profiles"), list):
            profiles = raw.get("profiles")
        if profiles is None and isinstance((a2.get("views") or {}).get("profiles_top"), list):
            profiles = (a2.get("views") or {}).get("profiles_top")
        if not isinstance(profiles, list):
            return []
        terms = []
        for profile in profiles:
            if isinstance(profile, dict) and profile.get("term"):
                terms.append(str(profile.get("term")))
            if len(terms) >= int(max_terms):
                break
        seen = set()
        out = []
        for term in terms:
            key = term.strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(term)
        return out
    except Exception:
        return []


def main() -> int:
    p = argparse.ArgumentParser(description="Per-term claims clustering (term consensus gap)")
    p.add_argument("--run-id", required=True)
    p.add_argument("--osh-ledger", default="out/osh_ledgers/fetch_artifacts.jsonl")
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument("--a2-phase", default=None, help="a2_phase_<run>.json (to supply term list)")
    p.add_argument("--sim-threshold", type=float, default=0.42)
    p.add_argument("--max-pairs", type=int, default=120000)
    p.add_argument("--max-per-source", type=int, default=5)
    p.add_argument("--min-overlap", type=int, default=1)
    p.add_argument("--max-terms-per-claim", type=int, default=4)
    p.add_argument("--max-terms", type=int, default=1500)
    p.add_argument("--min-claims-per-term", type=int, default=5)
    args = p.parse_args()

    ts = _utc_now_iso()
    sources, sig = load_sources_from_osh(args.osh_ledger)
    items = extract_claim_items_from_sources(
        sources,
        run_id=args.run_id,
        max_per_source=int(args.max_per_source),
    )

    ev_by_term = evidence_by_term("out/evidence_bundles")
    a2_path = args.a2_phase or os.path.join(args.out_reports, f"a2_phase_{args.run_id}.json")
    term_csp_map: Dict[str, Dict[str, Any]] = {}
    try:
        if os.path.exists(a2_path):
            with open(a2_path, "r", encoding="utf-8") as f:
                a2 = json.load(f)
            raw = a2.get("raw_full") if isinstance(a2, dict) else {}
            profiles = (
                raw.get("profiles")
                if isinstance(raw, dict) and isinstance(raw.get("profiles"), list)
                else None
            )
            if isinstance(profiles, list):
                for profile in profiles:
                    if not isinstance(profile, dict):
                        continue
                    term = str(profile.get("term") or "").strip().lower()
                    if term and isinstance(profile.get("term_csp_summary"), dict):
                        term_csp_map[term] = profile["term_csp_summary"]
    except Exception:
        term_csp_map = {}
    terms = _load_terms_from_a2(a2_path, max_terms=int(args.max_terms))
    term_tok = build_term_token_index([t.lower() for t in terms])

    term_bins: Dict[str, List[int]] = {}
    for ix, item in enumerate(items):
        claim = str(item.get("claim") or "")
        assigned = assign_claim_to_terms(
            claim,
            term_tok,
            min_overlap=int(args.min_overlap),
            max_terms=int(args.max_terms_per_claim),
        )
        for term in assigned:
            term_bins.setdefault(term, []).append(ix)

    term_clusters: Dict[str, List[List[int]]] = {}
    term_metrics: Dict[str, Dict[str, Any]] = {}
    support_cache: Dict[tuple[str, int], tuple[float, Dict[str, Any]]] = {}
    for term, ixs in term_bins.items():
        if len(ixs) < int(args.min_claims_per_term):
            continue
        sub_items: List[Dict[str, Any]] = []
        for i in ixs:
            item = items[i]
            text = str(item.get("claim") or "")
            key = (term, i)
            if key not in support_cache:
                support_cache[key] = support_weight_for_claim(
                    term=term,
                    claim_text=text,
                    evidence_by_term=ev_by_term,
                )
            bonus, dbg = support_cache[key]
            item.setdefault("evidence_support_weight_by_term", {})[term] = float(bonus)
            item.setdefault("evidence_support_debug_by_term", {})[term] = dbg
            current = float(item.get("evidence_support_weight") or 0.0)
            if bonus > current:
                item["evidence_support_weight"] = float(bonus)
                item["evidence_support_debug"] = dbg
            term_key = str(term).strip().lower()
            base_csp = term_csp_map.get(term_key, {})
            claim_csp = compute_claim_csp(
                claim_text=text,
                term_csp=base_csp,
                evidence_support_weight=float(bonus),
            )
            item.setdefault("claim_csp_by_term", {})[term] = claim_csp
            if not isinstance(item.get("claim_csp"), dict):
                item["claim_csp"] = claim_csp
            else:
                existing_cip = float(item.get("claim_csp", {}).get("CIP") or 0.0)
                if float(claim_csp.get("CIP") or 0.0) > existing_cip:
                    item["claim_csp"] = claim_csp
            cloned = dict(item)
            cloned["evidence_support_weight"] = float(bonus)
            cloned["evidence_support_debug"] = dbg
            cloned["claim_csp"] = claim_csp
            sub_items.append(cloned)
        clusters, metrics = cluster_claims(
            sub_items,
            sim_threshold=float(args.sim_threshold),
            max_pairs=int(args.max_pairs),
        )
        masses = []
        for cluster in clusters:
            mass = 0.0
            for idx in cluster:
                claim = sub_items[idx]
                mass += 1.0 + float(claim.get("evidence_support_weight") or 0.0)
            masses.append(mass)
        total = float(sum(masses))
        largest = float(max(masses)) if masses else 0.0
        consensus_gap = 1.0 - (largest / total) if total > 0 else 0.0
        global_clusters = [[ixs[j] for j in cluster] for cluster in clusters]
        term_clusters[term] = global_clusters
        metrics_dict = metrics.to_dict()
        metrics_dict["consensus_gap_unweighted"] = metrics_dict.get("consensus_gap")
        metrics_dict["consensus_gap"] = float(consensus_gap)
        metrics_dict["evidence_weighted"] = True
        term_metrics[term] = metrics_dict

    top_terms = sorted(
        [
            (
                term,
                float(metric.get("consensus_gap") or 0.0),
                int(metric.get("n_items") or 0),
            )
            for term, metric in term_metrics.items()
        ],
        key=lambda x: (-x[1], -x[2], x[0]),
    )[:30]

    core = {
        "version": "term_claims.v0.2",
        "run_id": args.run_id,
        "ts": ts,
        "metrics": {
            "n_terms": len(term_metrics),
            "term_consensus": term_metrics,
        },
        "views": {
            "top_terms_by_gap": [
                {"term": term, "consensus_gap": gap, "n_items": n}
                for (term, gap, n) in top_terms
            ]
        },
        "provenance": {
            "builder": "abx.term_claims_run.v0.2",
            "osh_ledger": args.osh_ledger,
            "a2_phase": a2_path,
            "sim_threshold": args.sim_threshold,
            "min_claims_per_term": args.min_claims_per_term,
        },
    }

    ctx = RuneInvocationContext(run_id=args.run_id, subsystem_id="abx.term_claims_run", git_hash="unknown")
    result = invoke_capability(
        "evolve.policy.enforce_non_truncation",
        {
            "artifact": core,
            "raw_full": {
                "sources": sources,
                "signals": sig,
                "items": items,
                "term_bins": term_bins,
                "term_clusters": term_clusters,
            },
        },
        ctx=ctx,
        strict_execution=True
    )
    out = result["artifact"]
    path = os.path.join(args.out_reports, f"term_claims_{args.run_id}.json")
    _write_json(path, out)
    print(f"[TERM_CLAIMS_RUN] wrote: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
