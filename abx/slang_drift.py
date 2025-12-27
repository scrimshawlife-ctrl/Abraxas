from __future__ import annotations

import argparse
import glob
import json
import os
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from abx.manufacture_score import manufacture_likelihood


_WORD = re.compile(r"[a-z0-9']+")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().replace(microsecond=0).isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _tokens(s: str) -> List[str]:
    return _WORD.findall((s or "").lower())


def _norm_term(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[\s\-_]+", " ", s)
    s = re.sub(r"[^a-z0-9' ]+", "", s)
    return s.strip()


def _skeleton(s: str) -> str:
    s = _norm_term(s)
    s = s.replace(" ", "").replace("'", "")
    if s.endswith("s") and len(s) > 4:
        s = s[:-1]
    return s


def _cosine_sparse(a: Dict[str, float], b: Dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    dot = 0.0
    for k, va in a.items():
        vb = b.get(k)
        if vb is not None:
            dot += float(va) * float(vb)
    na = sum(float(v) * float(v) for v in a.values()) ** 0.5
    nb = sum(float(v) * float(v) for v in b.values()) ** 0.5
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(dot) / float(na * nb)


def load_baseline_lexicon(path: Optional[str]) -> set[str]:
    if not path or not os.path.exists(path):
        return set()
    try:
        if path.endswith(".json"):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return {_norm_term(str(x)) for x in data if str(x).strip()}
            if isinstance(data, dict) and isinstance(data.get("terms"), list):
                return {_norm_term(str(x)) for x in data["terms"] if str(x).strip()}
        out = set()
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                t = _norm_term(line.strip())
                if t:
                    out.add(t)
        return out
    except Exception:
        return set()


def list_runs(out_reports: str, days: int) -> List[str]:
    now = _utc_now()
    cutoff = now - timedelta(days=days)
    paths = sorted(glob.glob(os.path.join(out_reports, "a2_phase_*.json")))
    run_ids: List[Tuple[float, str]] = []
    for path in paths:
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc)
            if mtime < cutoff:
                continue
        except Exception:
            continue
        rid = path.split("a2_phase_", 1)[-1].replace(".json", "")
        run_ids.append((mtime.timestamp(), rid))
    run_ids.sort(key=lambda x: (x[0], x[1]))
    return [rid for _, rid in run_ids]


def extract_terms_from_a2(a2: Dict[str, Any], limit: int = 200) -> List[str]:
    raw = a2.get("raw_full") if isinstance(a2, dict) else {}
    profs = raw.get("profiles") if isinstance(raw, dict) else None
    if not isinstance(profs, list):
        views = (a2.get("views") or {}).get("profiles_top") if isinstance(a2, dict) else None
        profs = views if isinstance(views, list) else []
    out = []
    for profile in profs:
        if not isinstance(profile, dict):
            continue
        term = str(profile.get("term") or "").strip()
        if term:
            out.append(term)
    seen = set()
    uniq = []
    for term in out:
        key = _norm_term(term)
        if key and key not in seen:
            uniq.append(term)
            seen.add(key)
        if len(uniq) >= limit:
            break
    return uniq


def extract_term_csp_map(a2: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    raw = a2.get("raw_full") if isinstance(a2, dict) else {}
    profs = raw.get("profiles") if isinstance(raw, dict) else None
    if not isinstance(profs, list):
        views = (a2.get("views") or {}).get("profiles_top") if isinstance(a2, dict) else None
        profs = views if isinstance(views, list) else []
    out: Dict[str, Dict[str, Any]] = {}
    for profile in profs:
        if not isinstance(profile, dict):
            continue
        term = str(profile.get("term") or "").strip()
        if not term:
            continue
        csp = (
            profile.get("term_csp_summary")
            if isinstance(profile.get("term_csp_summary"), dict)
            else {}
        )
        if not csp:
            continue
        out[_norm_term(term)] = {
            "COH": bool(csp.get("COH")),
            "tag": str(csp.get("tag") or "unknown"),
            "EA": float(csp.get("EA") or 0.0),
            "FF": float(csp.get("FF") or 0.0),
            "MIO": float(csp.get("MIO") or 0.0),
            "CIP": float(csp.get("CIP") or 0.0),
        }
    return out


def extract_fog_types(mwr_enriched: Dict[str, Any]) -> Dict[str, List[str]]:
    cw = (
        mwr_enriched.get("csp_weather")
        if isinstance(mwr_enriched.get("csp_weather"), dict)
        else {}
    )
    fi = cw.get("fog_index") if isinstance(cw.get("fog_index"), dict) else {}
    by_term = fi.get("by_term") if isinstance(fi.get("by_term"), dict) else {}
    out: Dict[str, List[str]] = {}
    for key, value in by_term.items():
        if isinstance(value, list):
            out[_norm_term(key)] = [str(x) for x in value]
    return out


def build_variant_clusters(terms: List[str]) -> Dict[str, Dict[str, Any]]:
    buckets: Dict[str, List[str]] = defaultdict(list)
    for term in terms:
        sk = _skeleton(term)
        if sk:
            buckets[sk].append(term)

    clusters: Dict[str, Dict[str, Any]] = {}
    for sk, variants in buckets.items():
        canonical = sorted(
            variants, key=lambda x: (len(_norm_term(x)), _norm_term(x))
        )[0]
        seen = set()
        uniq = []
        for x in sorted(variants, key=lambda y: (_norm_term(y), y)):
            nk = _norm_term(x)
            if nk not in seen:
                uniq.append(x)
                seen.add(nk)
        clusters[sk] = {"canonical_term": canonical, "variants": uniq}
    return clusters


def cooccurrence_context(
    runs_terms: List[List[str]], window_k: int = 25
) -> Dict[str, Dict[str, float]]:
    ctx: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for terms in runs_terms:
        tks = [_norm_term(t) for t in terms[:window_k] if _norm_term(t)]
        uniq = []
        seen = set()
        for tk in tks:
            if tk not in seen:
                uniq.append(tk)
                seen.add(tk)
        for i, a in enumerate(uniq):
            for j, b in enumerate(uniq):
                if i == j:
                    continue
                ctx[a][b] += 1.0
    return {k: dict(v) for k, v in ctx.items()}


def top_neighbors(vec: Dict[str, float], n: int = 8) -> List[Tuple[str, float]]:
    items = sorted(vec.items(), key=lambda x: (-float(x[1]), x[0]))
    return items[:n]


def run_slang_drift(
    *,
    out_reports: str,
    days: int,
    baseline_lexicon_path: Optional[str],
    per_run_terms_limit: int,
    cooc_window_k: int,
) -> Dict[str, Any]:
    run_ids = list_runs(out_reports, days)
    if not run_ids:
        return {
            "version": "slang_drift.v0.2",
            "ts": _utc_now_iso(),
            "days": days,
            "runs": [],
            "terms": [],
            "notes": "No runs in window.",
        }

    baseline = load_baseline_lexicon(baseline_lexicon_path)

    runs_terms: List[List[str]] = []
    runs_meta: List[Dict[str, Any]] = []

    for rid in run_ids:
        a2 = _read_json(os.path.join(out_reports, f"a2_phase_{rid}.json"))
        terms = extract_terms_from_a2(a2, limit=per_run_terms_limit)
        runs_terms.append(terms)

        mwr = _read_json(os.path.join(out_reports, f"mwr_{rid}.json"))
        dmx = mwr.get("dmx") if isinstance(mwr.get("dmx"), dict) else {}
        dmx_bucket = str(dmx.get("bucket") or "UNKNOWN").upper()
        dmx_overall = float(dmx.get("overall_manipulation_risk") or 0.0)

        mwr_en = _read_json(os.path.join(out_reports, f"mwr_enriched_{rid}.json"))
        fog_by_term = extract_fog_types(mwr_en)
        csp_map = extract_term_csp_map(a2)

        runs_meta.append(
            {
                "run_id": rid,
                "dmx_bucket": dmx_bucket,
                "dmx_overall": dmx_overall,
                "fog_by_term": fog_by_term,
                "csp_map": csp_map,
            }
        )

    mid = len(run_ids) // 2
    early_terms = runs_terms[:mid] if mid > 0 else runs_terms
    late_terms = runs_terms[mid:] if mid > 0 else runs_terms

    ctx_early = cooccurrence_context(early_terms, window_k=cooc_window_k)
    ctx_late = cooccurrence_context(late_terms, window_k=cooc_window_k)

    display_terms = []
    seen = set()
    for terms in runs_terms:
        for term in terms:
            nk = _norm_term(term)
            if nk and nk not in seen:
                display_terms.append(term)
                seen.add(nk)
    clusters = build_variant_clusters(display_terms)

    appearances: Dict[str, int] = defaultdict(int)
    first_seen: Dict[str, str] = {}
    last_seen: Dict[str, str] = {}
    dmx_bucket_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    fog_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    norm_csp_latest: Dict[str, Dict[str, Any]] = {}
    for idx, rid in enumerate(run_ids):
        meta = runs_meta[idx]
        bucket = meta["dmx_bucket"]
        fog_by_term = meta["fog_by_term"]
        csp_map = meta.get("csp_map") if isinstance(meta.get("csp_map"), dict) else {}
        for term in runs_terms[idx]:
            nk = _norm_term(term)
            if not nk:
                continue
            appearances[nk] += 1
            if nk not in first_seen:
                first_seen[nk] = rid
            last_seen[nk] = rid
            dmx_bucket_counts[nk][bucket] += 1
            for ft in fog_by_term.get(nk, []) or []:
                fog_counts[nk][ft] += 1
            csp_here = csp_map.get(nk)
            if csp_here:
                norm_csp_latest[nk] = csp_here

    norm_to_sk = {}
    sk_to_cluster = {}
    for sk, cluster in clusters.items():
        sk_to_cluster[sk] = cluster
        for variant in cluster["variants"]:
            norm_to_sk[_norm_term(variant)] = sk

    canon_entries: Dict[str, Dict[str, Any]] = {}
    for nk, n in appearances.items():
        sk = norm_to_sk.get(nk, _skeleton(nk))
        cluster = sk_to_cluster.get(
            sk, {"canonical_term": nk, "variants": [nk]}
        )
        canon = _norm_term(cluster["canonical_term"])
        cell = canon_entries.setdefault(
            canon,
            {
                "canonical_term": cluster["canonical_term"],
                "variants": cluster["variants"],
                "appearances": 0,
                "first_seen": "",
                "last_seen": "",
                "dmx_bucket_counts": {},
                "fog_type_counts": {},
                "novelty": {},
                "drift": {},
                "csp": {},
                "manufacture": {},
            },
        )
        cell["appearances"] += int(n)
        fs = first_seen.get(nk, "")
        ls = last_seen.get(nk, "")
        if fs and (not cell["first_seen"] or fs < cell["first_seen"]):
            cell["first_seen"] = fs
        if ls and (not cell["last_seen"] or ls > cell["last_seen"]):
            cell["last_seen"] = ls

        for b, c in dmx_bucket_counts[nk].items():
            cell["dmx_bucket_counts"][b] = int(cell["dmx_bucket_counts"].get(b, 0)) + int(c)
        for ft, c in fog_counts[nk].items():
            cell["fog_type_counts"][ft] = int(cell["fog_type_counts"].get(ft, 0)) + int(c)

        cspn = norm_csp_latest.get(nk)
        if cspn:
            cur = cell.get("csp") if isinstance(cell.get("csp"), dict) else {}
            if not cur:
                cell["csp"] = dict(cspn)
            else:
                cell["csp"] = {
                    "COH": bool(cur.get("COH")) or bool(cspn.get("COH")),
                    "tag": str(cur.get("tag") or cspn.get("tag") or "unknown"),
                    "EA": float(
                        min(
                            float(cur.get("EA") or 0.0),
                            float(cspn.get("EA") or 0.0),
                        )
                    ),
                    "FF": float(
                        min(
                            float(cur.get("FF") or 0.0),
                            float(cspn.get("FF") or 0.0),
                        )
                    ),
                    "MIO": float(
                        max(
                            float(cur.get("MIO") or 0.0),
                            float(cspn.get("MIO") or 0.0),
                        )
                    ),
                    "CIP": float(
                        max(
                            float(cur.get("CIP") or 0.0),
                            float(cspn.get("CIP") or 0.0),
                        )
                    ),
                }

    for canon, cell in canon_entries.items():
        in_baseline = canon in baseline if baseline else None
        early_seen = canon in ctx_early or any(
            _norm_term(v) in ctx_early for v in cell.get("variants", [])
        )
        late_seen = canon in ctx_late or any(
            _norm_term(v) in ctx_late for v in cell.get("variants", [])
        )

        cell["novelty"] = {
            "baseline_known": (not bool(baseline)) and None or (not in_baseline),
            "baseline_path": baseline_lexicon_path or "",
            "new_to_window": (not early_seen) and bool(late_seen),
        }

        ve = ctx_early.get(canon, {})
        vl = ctx_late.get(canon, {})
        sim = _cosine_sparse(ve, vl)
        drift_score = 1.0 - sim
        cell["drift"] = {
            "similarity_early_late": float(sim),
            "drift_score": float(drift_score),
            "early_neighbors": [
                {"term": k, "w": float(v)} for k, v in top_neighbors(ve, n=8)
            ],
            "late_neighbors": [
                {"term": k, "w": float(v)} for k, v in top_neighbors(vl, n=8)
            ],
        }
        cell["manufacture"] = manufacture_likelihood(cell)

    items = list(canon_entries.values())

    def _rank(x: Dict[str, Any]) -> Tuple[float, float, float, str]:
        ml = float((x.get("manufacture") or {}).get("ml_score") or 0.0)
        n2w = 1.0 if (x.get("novelty") or {}).get("new_to_window") else 0.0
        drift = float((x.get("drift") or {}).get("drift_score") or 0.0)
        app = float(x.get("appearances") or 0.0)
        return (-ml, -n2w, -drift, -app, _norm_term(str(x.get("canonical_term") or "")))

    items.sort(key=_rank)

    return {
        "version": "slang_drift.v0.2",
        "ts": _utc_now_iso(),
        "days": days,
        "runs": run_ids,
        "params": {
            "per_run_terms_limit": per_run_terms_limit,
            "cooc_window_k": cooc_window_k,
            "baseline_lexicon_path": baseline_lexicon_path or "",
            "baseline_loaded": bool(baseline),
        },
        "terms": items[:250],
        "notes": "Deterministic co-occurrence context drift. No embeddings. Variant clustering via skeleton normalization.",
    }


def main() -> int:
    p = argparse.ArgumentParser(
        description="Compute lexical novelty + variant clusters + semantic drift over last N days"
    )
    p.add_argument("--days", type=int, default=14)
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument(
        "--baseline-lexicon",
        default="",
        help="Optional txt/json lexicon for novelty detection",
    )
    p.add_argument("--per-run-terms-limit", type=int, default=200)
    p.add_argument("--cooc-window-k", type=int, default=25)
    p.add_argument(
        "--out",
        default="",
        help="Optional output path; defaults to out/reports/slang_drift_<stamp>.json",
    )
    args = p.parse_args()

    stamp = _utc_now().strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join(args.out_reports, f"slang_drift_{stamp}.json")
    obj = run_slang_drift(
        out_reports=args.out_reports,
        days=int(args.days),
        baseline_lexicon_path=(args.baseline_lexicon or None),
        per_run_terms_limit=int(args.per_run_terms_limit),
        cooc_window_k=int(args.cooc_window_k),
    )
    _write_json(out_path, obj)
    print(f"[SLANG_DRIFT] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
