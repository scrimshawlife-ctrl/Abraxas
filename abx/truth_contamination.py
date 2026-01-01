from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
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


def _latest(dir_path: str, pattern: str) -> str:
    paths = sorted(glob.glob(os.path.join(dir_path, pattern)))
    return paths[-1] if paths else ""


def _clamp(x: float, a: float = 0.0, b: float = 1.0) -> float:
    return float(max(a, min(b, x)))


def _sigmoid(x: float) -> float:
    # stable-ish sigmoid
    if x >= 0:
        z = 2.71828 ** (-x)
        return float(1.0 / (1.0 + z))
    z = 2.71828 ** (x)
    return float(z / (1.0 + z))


def _fingerprint(text: str) -> str:
    """
    Cheap template detector: normalize and hash.
    Helps detect repeated phrasing across claims/notes/anchors.
    """
    t = (text or "").lower().strip()
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    # drop very short stuff
    if len(t) < 20:
        return ""
    return hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]


def _quadrant(ml: float, cs: float) -> str:
    # thresholds can be tuned; keep deterministic
    ml_hi = ml >= 0.60
    cs_hi = cs >= 0.60
    if cs_hi and not ml_hi:
        return "LEGIT_PATTERN"
    if cs_hi and ml_hi:
        return "WEAPONIZED_TRUTH"
    if (not cs_hi) and ml_hi:
        return "LIKELY_MANIPULATION"
    return "BENIGN_NOISE"


def build_tpl_coord_from_ledgers(
    *,
    evidence_graph_ledger: str,
    anchor_ledger: str,
    window_runs: int = 14,
) -> Dict[str, Any]:
    """
    Derive template likelihood (TPL) + coordination proxy (COORD) from our ledgers.

    - TPL: repeated fingerprints across claim texts + offline notes.
    - COORD: same fingerprint appearing across >=2 domains in window.
    """
    evs = _read_jsonl(evidence_graph_ledger)
    anchors = _read_jsonl(anchor_ledger)

    # Determine run window based on anchor ledger tail (fast, deterministic)
    run_ids = []
    seen = set()
    for e in reversed(anchors[-5000:]):
        rid = str(e.get("run_id") or "")
        if rid and rid not in seen:
            run_ids.append(rid)
            seen.add(rid)
        if len(run_ids) >= window_runs:
            break
    allowed = set(run_ids)

    # claim texts
    claim_text_by_id = {}
    for e in evs:
        if str(e.get("kind") or "") == "claim_added" and str(e.get("run_id") or "") in allowed:
            cid = str(e.get("claim_id") or "")
            txt = str(e.get("text") or "")
            if cid:
                claim_text_by_id[cid] = txt

    # offline notes from anchor ledger
    note_texts = []
    for a in anchors:
        if str(a.get("kind") or "") != "anchor_added":
            continue
        if str(a.get("run_id") or "") not in allowed:
            continue
        # we don't store the note text (only hash) for privacy; so TPL from notes is limited.
        # However, URLs can also show templating via repeated paths/domains — we handle that elsewhere.
        # Keep this placeholder minimal.
        pass

    # fingerprint counts
    fp_claim = Counter()
    fp_to_claims = defaultdict(list)
    for cid, txt in claim_text_by_id.items():
        fp = _fingerprint(txt)
        if not fp:
            continue
        fp_claim[fp] += 1
        fp_to_claims[fp].append(cid)

    # domain coordination: if the same fingerprint appears across anchors from different domains linked to the claim
    # We'll approximate by scanning anchor_claim_link edges in evidence_graph_ledger and counting domains per fp.
    fp_domains = defaultdict(set)
    claim_fp = {}
    for cid, txt in claim_text_by_id.items():
        fp = _fingerprint(txt)
        if fp:
            claim_fp[cid] = fp

    for e in evs:
        if str(e.get("kind") or "") != "anchor_claim_link":
            continue
        if str(e.get("run_id") or "") not in allowed:
            continue
        cid = str(e.get("claim_id") or "")
        dom = str(e.get("domain") or "")
        fp = claim_fp.get(cid, "")
        if fp and dom:
            fp_domains[fp].add(dom)

    # compute TPL per claim: based on fingerprint repetition count
    tpl_by_claim = {}
    coord_by_claim = {}
    for cid, fp in claim_fp.items():
        reps = int(fp_claim.get(fp, 0))
        # template likelihood rises if same normalized text appears repeatedly
        tpl = _clamp((reps - 1) / 4.0)  # 0 at 1x, 1 at 5x+
        # coordination proxy rises if same template appears across many domains
        doms = len(fp_domains.get(fp, set()))
        coord = _clamp((doms - 1) / 3.0)  # 0 at 1 domain, 1 at 4+ domains
        tpl_by_claim[cid] = {"TPL": float(tpl), "repetitions": reps, "fp": fp}
        coord_by_claim[cid] = {"COORD": float(coord), "template_domains": doms, "fp": fp}

    return {
        "version": "tpl_coord.v0.1",
        "ts": _utc_now_iso(),
        "window_runs": int(window_runs),
        "n_claim_texts": len(claim_text_by_id),
        "tpl_by_claim": tpl_by_claim,
        "coord_by_claim": coord_by_claim,
        "notes": "TPL/COORD are cheap proxies derived from claim text fingerprints + multi-domain reuse.",
    }


def compute_truth_map(
    *,
    evidence_metrics_path: str,
    proof_integrity_path: str,
    sig_kpi_path: str,
    tpl_coord: Dict[str, Any],
    regime_shift_path: str = "",
) -> Dict[str, Any]:
    em = _read_json(evidence_metrics_path)
    pis_obj = _read_json(proof_integrity_path)
    sig = _read_json(sig_kpi_path)
    reg = _read_json(regime_shift_path) if regime_shift_path else {}

    pis = float(pis_obj.get("PIS") or 0.0) if isinstance(pis_obj, dict) else 0.0
    cs = em.get("claim_scores") if isinstance(em.get("claim_scores"), dict) else {}
    tpl_by = (tpl_coord.get("tpl_by_claim") or {}) if isinstance(tpl_coord.get("tpl_by_claim"), dict) else {}
    coord_by = (tpl_coord.get("coord_by_claim") or {}) if isinstance(tpl_coord.get("coord_by_claim"), dict) else {}

    # global helpers from SIG/PDG to calibrate thresholds
    pdg = sig.get("PDG") if isinstance(sig.get("PDG"), dict) else {}
    avg_domains = float(pdg.get("avg_unique_domains_per_term") or 0.0)
    avg_tests = float(pdg.get("avg_falsification_tests_per_term") or 0.0)

    regime = bool(reg.get("regime_shift")) if isinstance(reg, dict) else False
    regime_boost = 0.08 if regime else 0.0  # in regime shift, treat manipulation likelihood slightly higher (truth is noisier)

    out_claims = {}
    for cid, v in cs.items():
        if not isinstance(v, dict):
            continue
        CSS = float(v.get("CSS") or 0.0)
        CPR = float(v.get("CPR") or 0.0)
        supp_dom = float(v.get("support_domains") or 0.0)
        contra_dom = float(v.get("contra_domains") or 0.0)

        tpl = float((tpl_by.get(cid) or {}).get("TPL") or 0.0)
        coord = float((coord_by.get(cid) or {}).get("COORD") or 0.0)

        # --- Coherence Strength (CS_score) ---
        # High CSS good; high CPR bad; diversity helps; falsification culture helps (global proxy)
        div = _clamp((supp_dom + 0.5 * contra_dom) / 6.0)
        fals_culture = _clamp(avg_tests / 3.0)
        cs_score = _clamp(0.60 * CSS + 0.20 * div + 0.20 * fals_culture - 0.12 * _clamp(CPR / 2.0))

        # --- Manipulation Likelihood (ML_score) ---
        # High TPL/COORD increases ML. Low PIS increases ML. High SDR would too, but SDR is domain-level; keep for WO-74.
        low_pis = _clamp(1.0 - pis)
        ml_score = _clamp(
            0.42 * tpl
            + 0.28 * coord
            + 0.22 * low_pis
            + 0.10 * _clamp(1.0 - (avg_domains / 6.0))  # low diversity environment increases risk
            + regime_boost
        )

        quad = _quadrant(ml_score, cs_score)
        out_claims[cid] = {
            "CS_score": float(cs_score),
            "ML_score": float(ml_score),
            "quadrant": quad,
            "inputs": {
                "CSS": float(CSS),
                "CPR": float(CPR),
                "support_domains": int(supp_dom),
                "contra_domains": int(contra_dom),
                "TPL": float(tpl),
                "COORD": float(coord),
                "PIS": float(pis),
                "avg_unique_domains_per_term": float(avg_domains),
                "avg_falsification_tests_per_term": float(avg_tests),
                "regime_shift": bool(regime),
            },
            "notes": "Two-axis classification: Manipulation Likelihood × Coherence Strength. No censorship; only flags.",
        }

    # simple summary counts
    quad_counts = Counter([v.get("quadrant") for v in out_claims.values()])
    return {
        "version": "truth_contamination.v0.1",
        "ts": _utc_now_iso(),
        "paths": {
            "evidence_metrics": evidence_metrics_path,
            "proof_integrity": proof_integrity_path,
            "sig_kpi": sig_kpi_path,
            "regime_shift": regime_shift_path or None,
        },
        "globals": {
            "PIS": float(pis),
            "avg_unique_domains_per_term": float(avg_domains),
            "avg_falsification_tests_per_term": float(avg_tests),
            "regime_shift": bool(regime),
        },
        "quadrant_counts": dict(quad_counts),
        "claims": out_claims,
        "notes": "Two-axis map supports distinguishing engineered pollution from legitimate conspiratorial observation.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Compute Truth Contamination Map (Manipulation × Coherence)")
    ap.add_argument("--evidence-metrics", default="")
    ap.add_argument("--proof-integrity", default="")
    ap.add_argument("--sig-kpi", default="")
    ap.add_argument("--regime-shift", default="")
    ap.add_argument("--evidence-graph-ledger", default="out/ledger/evidence_graph.jsonl")
    ap.add_argument("--anchor-ledger", default="out/ledger/anchor_ledger.jsonl")
    ap.add_argument("--window-runs", type=int, default=14)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    em = args.evidence_metrics or _latest("out/reports", "evidence_metrics_*.json")
    pis = args.proof_integrity or _latest("out/reports", "proof_integrity_*.json")
    sig = args.sig_kpi or _latest("out/reports", "sig_kpi_*.json")
    reg = args.regime_shift or _latest("out/reports", "regime_shift_*.json")

    tpl_coord = build_tpl_coord_from_ledgers(
        evidence_graph_ledger=args.evidence_graph_ledger,
        anchor_ledger=args.anchor_ledger,
        window_runs=int(args.window_runs),
    )

    obj = compute_truth_map(
        evidence_metrics_path=em,
        proof_integrity_path=pis,
        sig_kpi_path=sig,
        tpl_coord=tpl_coord,
        regime_shift_path=reg,
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join("out/reports", f"truth_contamination_{stamp}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[TRUTH_MAP] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
