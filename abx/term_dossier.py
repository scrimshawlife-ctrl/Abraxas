from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def _read_jsonl(path: str, max_lines: int = 500000) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    out: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                out.append(obj)
    return out


def _slug(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:80] if text else "term"


def _bucket(value: float) -> str:
    if value >= 0.70:
        return "HIGH"
    if value >= 0.40:
        return "MED"
    return "LOW"


def _find_profile(a2: Dict[str, Any], term: str) -> Dict[str, Any]:
    term_k = term.strip().lower()
    raw = a2.get("raw_full") or {}
    profs = []
    if isinstance(raw, dict) and isinstance(raw.get("profiles"), list):
        profs = raw.get("profiles")
    elif isinstance((a2.get("views") or {}).get("profiles_top"), list):
        profs = (a2.get("views") or {}).get("profiles_top")
    for profile in profs:
        if isinstance(profile, dict) and str(profile.get("term") or "").strip().lower() == term_k:
            return profile
    return {}


def _term_clusters(
    term_claims: Dict[str, Any],
    term: str,
    items: List[Dict[str, Any]],
    max_clusters: int = 6,
) -> List[Dict[str, Any]]:
    term_k = term.strip().lower()
    raw = term_claims.get("raw_full") or {}
    clusters_map = raw.get("term_clusters") if isinstance(raw, dict) else {}
    if not isinstance(clusters_map, dict):
        return []
    clusters = clusters_map.get(term_k) or clusters_map.get(term) or []
    if not isinstance(clusters, list):
        return []
    out = []
    for cluster in clusters[:max_clusters]:
        if not isinstance(cluster, list) or not cluster:
            continue
        rep = items[cluster[0]].get("claim") if cluster[0] < len(items) else ""
        domains = sorted({(items[i].get("domain") or "") for i in cluster if i < len(items)})[:10]
        out.append({"n": len(cluster), "rep": rep, "domains": domains})
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="Emit a Term Dossier (export artifact)")
    p.add_argument("--run-id", required=True)
    p.add_argument("--term", required=True)
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument("--pred-ledger", default="out/forecast_ledger/predictions.jsonl")
    args = p.parse_args()

    ts = _utc_now_iso()
    term = args.term
    slug = _slug(term)

    a2 = _read_json(os.path.join(args.out_reports, f"a2_phase_{args.run_id}.json"))
    mwr = _read_json(os.path.join(args.out_reports, f"mwr_{args.run_id}.json"))
    term_claims = _read_json(os.path.join(args.out_reports, f"term_claims_{args.run_id}.json"))

    profile = _find_profile(a2, term)
    dmx = (mwr.get("dmx") or {}) if isinstance(mwr, dict) else {}
    overall = float(dmx.get("overall_manipulation_risk") or 0.0)
    bucket = str(dmx.get("bucket") or _bucket(overall))

    tc_raw = term_claims.get("raw_full") if isinstance(term_claims, dict) else {}
    items = (tc_raw.get("items") or []) if isinstance(tc_raw, dict) else []
    clusters_view = _term_clusters(term_claims, term, items)

    preds = _read_jsonl(args.pred_ledger)
    term_k = term.strip().lower()
    touched = []
    for pr in preds:
        t = str(pr.get("term") or "").strip().lower()
        ts_list = pr.get("terms") if isinstance(pr.get("terms"), list) else []
        ts_list_k = [str(x).strip().lower() for x in ts_list]
        if t == term_k or term_k in ts_list_k:
            touched.append(pr)

    md_path = os.path.join(args.out_reports, f"term_dossier_{args.run_id}__{slug}.md")
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Term Dossier — {term}\n\n")
        f.write(f"- run_id: `{args.run_id}`\n")
        f.write(f"- ts: `{ts}`\n\n")

        f.write("## Environment (MWR / DMX)\n")
        f.write(f"- overall_manipulation_risk: **{overall:.3f}**\n")
        f.write(f"- bucket: **{bucket}**\n\n")

        f.write("## Term Profile (A2)\n")
        if not profile:
            f.write("- profile not found in a2_phase\n\n")
        else:
            f.write(f"- phase: `{profile.get('phase')}`\n")
            f.write(f"- v14: `{profile.get('v14')}`\n")
            f.write(f"- v60: `{profile.get('v60')}`\n")
            f.write(f"- half_life_days_fit: `{profile.get('half_life_days_fit')}`\n")
            f.write(f"- manipulation_risk_mean: `{profile.get('manipulation_risk_mean')}`\n")
            f.write(f"- consensus_gap_term: `{profile.get('consensus_gap_term')}`\n\n")

        f.write("## Claim Clusters (term-conditioned)\n")
        if not clusters_view:
            f.write("- no clusters (or insufficient claims)\n\n")
        else:
            for i, c in enumerate(clusters_view, 1):
                f.write(f"{i}. n={c['n']}  rep: {c['rep']}\n")
                if c["domains"]:
                    f.write(f"   - domains: {', '.join(c['domains'])}\n")
            f.write("\n")

        f.write("## Predictions touching term\n")
        f.write(f"- count: **{len(touched)}**\n\n")
        for pr in touched[:20]:
            f.write(
                f"- pred_id={pr.get('pred_id')}  horizon={pr.get('horizon')}  p={pr.get('p')}\n"
            )
            if pr.get("flags"):
                f.write(f"  - flags: {pr.get('flags')}\n")
            ctx = pr.get("context") if isinstance(pr.get("context"), dict) else {}
            gate = ctx.get("gate") if isinstance(ctx, dict) else {}
            if isinstance(gate, dict) and gate:
                f.write(
                    "  - gate: "
                    f"horizon_max={gate.get('horizon_max')} "
                    f"eeb_mul={gate.get('eeb_multiplier')} "
                    f"esc={gate.get('evidence_escalation')}\n"
                )
        f.write("\n")

    js_path = os.path.join(args.out_reports, f"term_dossier_{args.run_id}__{slug}.json")
    with open(js_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "version": "term_dossier.v0.1",
                "run_id": args.run_id,
                "ts": ts,
                "term": term,
                "dmx": {"overall_manipulation_risk": overall, "bucket": bucket},
                "profile": profile,
                "clusters_view": clusters_view,
                "predictions_touching_term": touched,
                "provenance": {"builder": "abx.term_dossier.v0.1"},
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"[TERM_DOSSIER] wrote: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
