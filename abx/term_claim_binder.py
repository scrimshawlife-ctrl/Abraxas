from __future__ import annotations

import argparse
import glob
import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not path or not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                if isinstance(d, dict):
                    out.append(d)
            except Exception:
                continue
    return out


def _append_jsonl(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def _domain_group(domain: str) -> str:
    d = (domain or "").lower()
    if any(
        x in d
        for x in [
            "tiktok.com",
            "instagram.com",
            "youtube.com",
            "reddit.com",
            "twitter.com",
            "x.com",
        ]
    ):
        return "social"
    if any(
        x in d
        for x in [
            "wikipedia.org",
            "nih.gov",
            "nature.com",
            "science.org",
            "arxiv.org",
        ]
    ):
        return "reference"
    if any(
        x in d
        for x in [
            "nytimes.com",
            "bbc.co.uk",
            "reuters.com",
            "apnews.com",
            "theguardian.com",
        ]
    ):
        return "mainstream"
    if not d:
        return "none"
    return "other"


def _term_hits_in_anchor(term: str, title: str, hint: str) -> int:
    """
    Deterministic hit counter.
    - exact substring match for phrases
    - token-boundary match for single tokens
    """
    t = _norm(term)
    blob = _norm(f"{title} {hint}")
    if not t or not blob:
        return 0
    if " " in t:
        return 1 if t in blob else 0
    pat = re.compile(rf"(^|[^a-z0-9_]){re.escape(t)}([^a-z0-9_]|$)")
    return 1 if pat.search(blob) else 0


def build_term_index(
    anchors: List[Dict[str, Any]],
    terms: List[str],
) -> Dict[str, Dict[str, Any]]:
    """
    Returns index:
      term -> {
        "claim_scores": {claim_id: score},
        "claim_domain_groups": {claim_id: [groups]},
        "tot_score": float
      }
    """
    idx: Dict[str, Dict[str, Any]] = {}
    terms_n = [t for t in (str(x).strip() for x in terms) if t]
    if not terms_n:
        return {}

    for term in terms_n:
        claim_scores: Dict[str, float] = defaultdict(float)
        claim_groups: Dict[str, set] = defaultdict(set)
        for a in anchors:
            if not isinstance(a, dict):
                continue
            cid = str(a.get("claim_id") or "").strip()
            if not cid:
                continue
            title = str(a.get("title") or "")
            hint = str(a.get("content_hint") or "")
            domain = str(a.get("domain") or "")
            hits = _term_hits_in_anchor(term, title, hint)
            if hits <= 0:
                continue
            claim_scores[cid] += 1.0
            claim_groups[cid].add(_domain_group(domain))

        for cid, groups in claim_groups.items():
            g = len([x for x in groups if x and x != "none"])
            claim_scores[cid] += 0.35 * min(3, g)

        tot = float(sum(claim_scores.values())) if claim_scores else 0.0
        idx[term] = {
            "claim_scores": dict(claim_scores),
            "claim_domain_groups": {
                cid: sorted(list(gs)) for cid, gs in claim_groups.items()
            },
            "tot_score": tot,
        }

    return idx


def bind_tasks(
    *,
    tasks_outbox: Dict[str, Any],
    term_index: Dict[str, Dict[str, Any]],
    bind_ratio: float,
    min_hits: float,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    tasks = (
        tasks_outbox.get("tasks")
        if isinstance(tasks_outbox.get("tasks"), list)
        else []
    )
    bound = []
    stats = {"n_in": len(tasks), "n_bound": 0, "n_unbound": 0}

    for t in tasks:
        if not isinstance(t, dict):
            continue
        term = str(t.get("term") or "").strip()
        if not term or term not in term_index:
            tt = dict(t)
            tt["binding"] = {"status": "UNBOUND", "reason": "no_term_index"}
            bound.append(tt)
            stats["n_unbound"] += 1
            continue

        info = term_index[term]
        scores = (
            info.get("claim_scores")
            if isinstance(info.get("claim_scores"), dict)
            else {}
        )
        tot = float(info.get("tot_score") or 0.0)
        if not scores or tot <= 0:
            tt = dict(t)
            tt["binding"] = {"status": "UNBOUND", "reason": "no_scores"}
            bound.append(tt)
            stats["n_unbound"] += 1
            continue

        best = sorted(scores.items(), key=lambda kv: (-float(kv[1]), kv[0]))[0]
        best_cid, best_score = str(best[0]), float(best[1])
        ratio = best_score / tot if tot > 0 else 0.0

        tt = dict(t)
        if best_score >= float(min_hits) and ratio >= float(bind_ratio):
            tt["claim_id"] = best_cid
            tt["binding"] = {
                "status": "BOUND",
                "claim_id": best_cid,
                "best_score": float(best_score),
                "tot_score": float(tot),
                "ratio": float(ratio),
                "domain_groups": (info.get("claim_domain_groups") or {}).get(
                    best_cid, []
                ),
            }
            stats["n_bound"] += 1
        else:
            tt["binding"] = {
                "status": "UNBOUND",
                "reason": "threshold_fail",
                "best_claim_id": best_cid,
                "best_score": float(best_score),
                "tot_score": float(tot),
                "ratio": float(ratio),
            }
            stats["n_unbound"] += 1

        bound.append(tt)

    out = dict(tasks_outbox)
    out["tasks"] = bound
    out["binding_stats"] = stats
    out["binding_policy"] = {
        "bind_ratio": float(bind_ratio),
        "min_hits": float(min_hits),
    }
    return out, stats


def main() -> int:
    ap = argparse.ArgumentParser(
        description="WO-89: bind term-driven weather tasks to claim_ids using anchor ledger index"
    )
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--anchor-ledger", default="out/ledger/anchor_ledger.jsonl")
    ap.add_argument(
        "--tasks", default="", help="Path to weather_tasks_*.json (default: latest)"
    )
    ap.add_argument("--out", default="")
    ap.add_argument("--binder-ledger", default="out/ledger/binder_ledger.jsonl")
    ap.add_argument("--bind-ratio", type=float, default=0.62)
    ap.add_argument("--min-hits", type=float, default=2.0)
    ap.add_argument("--max-terms", type=int, default=40)
    args = ap.parse_args()

    if not args.tasks:
        wp = sorted(glob.glob("out/reports/weather_tasks_*.json"))
        args.tasks = wp[-1] if wp else ""
    if not args.tasks:
        raise SystemExit("No weather_tasks outbox found.")

    anchors = _read_jsonl(args.anchor_ledger)
    tasks_outbox = _read_json(args.tasks)
    tasks = (
        tasks_outbox.get("tasks")
        if isinstance(tasks_outbox.get("tasks"), list)
        else []
    )
    terms = []
    for t in tasks:
        if isinstance(t, dict):
            term = str(t.get("term") or "").strip()
            if term and term not in terms:
                terms.append(term)
    terms = terms[: int(args.max_terms)]

    idx = build_term_index(anchors, terms)
    bound_outbox, stats = bind_tasks(
        tasks_outbox=tasks_outbox,
        term_index=idx,
        bind_ratio=float(args.bind_ratio),
        min_hits=float(args.min_hits),
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join(
        "out/reports", f"weather_tasks_bound_{stamp}.json"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(bound_outbox, f, ensure_ascii=False, indent=2)

    _append_jsonl(
        args.binder_ledger,
        {
            "kind": "term_claim_binding",
            "ts": _utc_now_iso(),
            "run_id": args.run_id,
            "in_tasks": args.tasks,
            "out_tasks": out_path,
            "stats": stats,
            "policy": {
                "bind_ratio": float(args.bind_ratio),
                "min_hits": float(args.min_hits),
                "max_terms": int(args.max_terms),
            },
            "notes": "WO-89 binds term-driven tasks to claim_ids using anchor ledger hit scoring + domain-group bonus.",
        },
    )

    print(
        f"[BINDER] wrote: {out_path} bound={stats['n_bound']} unbound={stats['n_unbound']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
