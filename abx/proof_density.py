from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = " ".join(s.replace("-", " ").replace("_", " ").split())
    return s


def _load_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _load_jsonl(path: str, run_id: str = "") -> List[Dict[str, Any]]:
    if not path or not os.path.exists(path):
        return []
    out = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    if not isinstance(d, dict):
                        continue
                    if run_id and str(d.get("run_id") or "") != str(run_id):
                        continue
                    out.append(d)
                except Exception:
                    continue
    except Exception:
        return []
    return out


def compute_proof_density(
    *,
    out_reports: str,
    ledger_path: str,
    run_ids: List[str],
    tpi_threshold: float = 0.45,
) -> Dict[str, Any]:
    """
    Proof density focuses on high-pollution / high-impact terms.
    - primary_anchors_per_term
    - diversity (unique domains)
    - falsification_tests_per_term (if tagged)
    """
    per_term = defaultdict(lambda: {"primary": 0, "events": 0, "domains": set(), "fals_tests": 0, "runs": set(), "tpi_max": 0.0})

    # load TPI per run and choose target terms
    target_terms = set()
    tpi_by_term = defaultdict(float)
    for rid in run_ids:
        tpi_path = os.path.join(out_reports, f"tpi_{rid}.json")
        t = _load_json(tpi_path)
        per = t.get("per_term") if isinstance(t.get("per_term"), dict) else {}
        for tk, v in per.items():
            try:
                tv = float((v or {}).get("tpi") or 0.0)
            except Exception:
                tv = 0.0
            nt = _norm(tk)
            if tv >= float(tpi_threshold):
                target_terms.add(nt)
            if tv > tpi_by_term[nt]:
                tpi_by_term[nt] = tv

    # scan ledger for those terms across runs
    for rid in run_ids:
        events = _load_jsonl(ledger_path, run_id=rid)
        for ev in events:
            term = _norm(str(ev.get("term") or ""))
            if not term or (target_terms and term not in target_terms):
                continue
            tags = ev.get("tags") if isinstance(ev.get("tags"), list) else []
            kind = str(ev.get("kind") or "")
            src = str(ev.get("source") or "")
            per_term[term]["events"] += 1
            per_term[term]["runs"].add(rid)
            per_term[term]["tpi_max"] = max(float(per_term[term]["tpi_max"]), float(tpi_by_term.get(term, 0.0)))
            if "primary" in tags or "official" in tags:
                per_term[term]["primary"] += 1
            if "falsification" in tags or "test" in tags:
                per_term[term]["fals_tests"] += 1
            # domain extraction (simple)
            if kind == "url":
                try:
                    dom = src.split("//", 1)[-1].split("/", 1)[0].lower()
                    if dom:
                        per_term[term]["domains"].add(dom)
                except Exception:
                    pass

    # summarize
    terms_out = []
    for term, st in per_term.items():
        domains = sorted(list(st["domains"]))
        terms_out.append({
            "term": term,
            "tpi_max": float(st["tpi_max"]),
            "runs": sorted(list(st["runs"])),
            "events": int(st["events"]),
            "primary_anchors": int(st["primary"]),
            "unique_domains": int(len(domains)),
            "domains_sample": domains[:12],
            "falsification_tests": int(st["fals_tests"]),
        })
    terms_out.sort(key=lambda x: (-float(x["tpi_max"]), -int(x["primary_anchors"]), -int(x["unique_domains"])))

    # global rollups
    n_terms = len(terms_out)
    if n_terms:
        avg_primary = sum(int(t["primary_anchors"]) for t in terms_out) / float(n_terms)
        avg_domains = sum(int(t["unique_domains"]) for t in terms_out) / float(n_terms)
        avg_tests = sum(int(t["falsification_tests"]) for t in terms_out) / float(n_terms)
    else:
        avg_primary = avg_domains = avg_tests = 0.0

    return {
        "version": "proof_density.v0.1",
        "ts": _utc_now_iso(),
        "run_ids": run_ids,
        "tpi_threshold": float(tpi_threshold),
        "n_terms": n_terms,
        "avg_primary_anchors_per_term": float(avg_primary),
        "avg_unique_domains_per_term": float(avg_domains),
        "avg_falsification_tests_per_term": float(avg_tests),
        "terms": terms_out[:200],
        "notes": "Proof density focuses on elevated TPI terms; it quantifies anchors + diversity + falsification tests.",
    }
