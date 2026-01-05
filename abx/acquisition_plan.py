from __future__ import annotations

import argparse
import glob
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from abraxas.acquire.decodo_client import build_decodo_query, decodo_status
from abraxas.acquire.vector_map_schema import default_vector_map_v0_1
from abraxas.conspiracy.csp import compute_term_csp
from abx.ml_index import load_ml_map
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    return d if isinstance(d, dict) else {}


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _profiles(a2: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = a2.get("raw_full") if isinstance(a2, dict) else {}
    profs = raw.get("profiles") if isinstance(raw, dict) else None
    if isinstance(profs, list):
        return [p for p in profs if isinstance(p, dict)]
    views = (a2.get("views") or {}).get("profiles_top") if isinstance(a2, dict) else None
    return (
        [p for p in views if isinstance(views, list) and isinstance(p, dict)]
        if isinstance(views, list)
        else []
    )


def _dmx(mwr: Dict[str, Any]) -> Dict[str, Any]:
    d = mwr.get("dmx") if isinstance(mwr, dict) else {}
    return d if isinstance(d, dict) else {}


def _missing_signals(p: Dict[str, Any], dmx_overall: float) -> List[str]:
    """
    Deterministic gap detection. Produces labeled 'what to acquire'.
    """
    missing = []
    att = float(p.get("attribution_strength") or 0.0)
    sd = float(p.get("source_diversity") or 0.0)
    cg = float(p.get("consensus_gap_term") or 0.0)
    mr = float(p.get("manipulation_risk") or 0.0)

    if att < 0.55:
        missing.append("NEED_ATTRIBUTION_STRONGER")
    if sd < 0.45:
        missing.append("NEED_SOURCE_DIVERSITY")
    if cg >= 0.60:
        missing.append("NEED_CONSENSUS_RESOLUTION")
    if mr >= 0.75:
        missing.append("NEED_MANIPULATION_TRIAGE")
    if dmx_overall >= 0.70:
        missing.append("HIGH_FOG_VERIFY_WITH_HIGH_CRED_SOURCES")
    return missing


def main() -> int:
    p = argparse.ArgumentParser(
        description="Build an Acquisition Plan (expand net, compound value)"
    )
    p.add_argument("--run-id", required=True)
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument("--vector-map", default=None, help="Optional override JSON for vector map")
    p.add_argument("--max-terms", type=int, default=20)
    args = p.parse_args()

    # Create rune context for capability invocations
    ctx = RuneInvocationContext(run_id=args.run_id, subsystem_id="abx.acquisition_plan", git_hash="unknown")

    ts = _utc_now_iso()
    a2_path = os.path.join(args.out_reports, f"a2_phase_{args.run_id}.json")
    mwr_path = os.path.join(args.out_reports, f"mwr_{args.run_id}.json")

    a2 = _read_json(a2_path)
    mwr = _read_json(mwr_path)
    dmx = _dmx(mwr)
    dmx_overall = float(dmx.get("overall_manipulation_risk") or 0.0)
    dmx_bucket = str(dmx.get("bucket") or "UNKNOWN").upper()

    vm = _read_json(args.vector_map) if args.vector_map else default_vector_map_v0_1()
    ds = decodo_status().to_dict()
    ml_map, ml_meta = load_ml_map(args.out_reports)
    cal_tasks = []
    try:
        paths = sorted(glob.glob(os.path.join(args.out_reports, "calibration_tasks_*.json")))
        if paths:
            obj = _read_json(paths[-1])
            cal_tasks = obj.get("tasks") if isinstance(obj.get("tasks"), list) else []
    except Exception:
        cal_tasks = []

    profs = _profiles(a2)

    def score(p0: Dict[str, Any]) -> float:
        mr = float(p0.get("manipulation_risk") or 0.0)
        cg = float(p0.get("consensus_gap_term") or 0.0)
        att = float(p0.get("attribution_strength") or 0.0)
        sd = float(p0.get("source_diversity") or 0.0)
        return (1.2 * mr) + (1.0 * cg) + (0.8 * (1.0 - att)) + (0.6 * (1.0 - sd))

    profs_sorted = sorted(
        profs, key=lambda x: (-score(x), str(x.get("term") or ""))
    )[: int(args.max_terms)]

    targets = []
    actions: List[Dict[str, Any]] = []

    channels = vm.get("channels") if isinstance(vm, dict) else []
    channels = [c for c in channels if isinstance(c, dict) and c.get("enabled")]

    for p0 in profs_sorted:
        term = str(p0.get("term") or "").strip()
        if not term:
            continue
        classify_result = invoke_capability(
            "forecast.term.classify",
            {"profile": p0},
            ctx=ctx,
            strict_execution=True
        )
        tcls = classify_result["classification"]
        miss = _missing_signals(p0, dmx_overall)
        csp = compute_term_csp(
            term=term,
            profile=p0,
            dmx_bucket=dmx_bucket,
            dmx_overall=dmx_overall,
            term_class=tcls,
        )
        if float(csp.get("EA") or 0.0) < 0.50:
            miss.append("CSP_NEED_EVIDENCE_ADEQUACY")
        if float(csp.get("FF") or 0.0) < 0.50:
            miss.append("CSP_NEED_FALSIFIABILITY_TESTS")
        if (
            bool(csp.get("COH"))
            and float(csp.get("CIP") or 0.0) >= 0.55
            and float(csp.get("EA") or 0.0) < 0.60
        ):
            miss.append("CSP_PLAUSIBLE_UNPROVEN_NEED_PRIMARY_DOCS")
        term_key = " ".join(term.lower().replace("-", " ").replace("_", " ").split())
        ml = ml_map.get(term_key)
        if isinstance(ml, dict):
            miss.append(f"ML_BUCKET_{str(ml.get('bucket') or 'UNKNOWN')}")
            score = float(ml.get("ml_score") or 0.0)
            if score >= 0.67:
                miss.append("ML_HIGH_STEERING_RISK")
            elif score >= 0.34:
                miss.append("ML_MED_STEERING_RISK")
            else:
                miss.append("ML_LOW_STEERING_RISK")
        targets.append(
            {"term": term, "class": tcls, "missing": miss, "csp": csp, "ml": ml or {}}
        )

        for ch in channels:
            ch_id = str(ch.get("id"))
            kind = str(ch.get("kind"))
            mode = str(ch.get("mode"))
            domains = ch.get("domains") if isinstance(ch.get("domains"), list) else []

            if mode == "manual_offline":
                if (
                    "NEED_ATTRIBUTION_STRONGER" in miss
                    or "HIGH_FOG_VERIFY_WITH_HIGH_CRED_SOURCES" in miss
                    or "CSP_NEED_EVIDENCE_ADEQUACY" in miss
                    or "CSP_PLAUSIBLE_UNPROVEN_NEED_PRIMARY_DOCS" in miss
                ):
                    actions.append(
                        {
                            "term": term,
                            "channel": ch_id,
                            "mode": "manual_offline",
                            "action": "prompt_user_for_artifacts",
                            "prompt": (
                                f"Provide 3 primary-source items for '{term}' "
                                "(docs, filings, direct statements, PDFs, screenshots). "
                                "Include origin, date, and the exact claim each item supports or contradicts."
                            ),
                            "rationale": miss,
                        }
                    )
                if "CSP_NEED_FALSIFIABILITY_TESTS" in miss:
                    actions.append(
                        {
                            "term": term,
                            "channel": ch_id,
                            "mode": "manual_offline",
                            "action": "prompt_user_for_falsification_tests",
                            "prompt": (
                                f"For '{term}', write 2-3 disconfirming tests: what evidence would prove "
                                "this coordination hypothesis wrong? Also list 1-2 differentiators that "
                                "separate organic confusion from coordinated operation."
                            ),
                            "rationale": miss,
                        }
                    )
                if "ML_HIGH_STEERING_RISK" in miss:
                    actions.append(
                        {
                            "term": term,
                            "channel": ch_id,
                            "mode": "manual_offline",
                            "action": "prompt_user_for_origin_trace",
                            "prompt": (
                                f"For '{term}', capture an origin trace: earliest timestamp you saw it, where "
                                "you saw it, and 3 earlier references if you can locate them. Note whether the "
                                "phrasing is identical across posts."
                            ),
                            "rationale": miss,
                        }
                    )
                    actions.append(
                        {
                            "term": term,
                            "channel": ch_id,
                            "mode": "manual_offline",
                            "action": "prompt_user_for_boost_signals",
                            "prompt": (
                                f"For '{term}', note boost signals: sudden appearance across accounts, repeated "
                                "templates, unusual repost velocity, or synchronized posting times. Provide 3 "
                                "example posts with timestamps."
                            ),
                            "rationale": miss,
                        }
                    )
                continue

            if mode == "decodo":
                if not ds.get("available"):
                    actions.append(
                        {
                            "term": term,
                            "channel": ch_id,
                            "mode": "decodo",
                            "action": "blocked_missing_decodo",
                            "rationale": ["DECODO_UNAVAILABLE", ds.get("reason")] + miss,
                        }
                    )
                    continue

                if dmx_bucket == "HIGH" and kind in ("forums", "video"):
                    continue
                if tcls in ("contested", "volatile") and kind in ("forums", "video"):
                    continue

                q = build_decodo_query(term, domains=domains)
                actions.append(
                    {
                        "term": term,
                        "channel": ch_id,
                        "mode": "decodo",
                        "action": "search",
                        "query": q,
                        "rationale": miss,
                    }
                )
                if "ML_HIGH_STEERING_RISK" in miss:
                    actions.append(
                        {
                            "term": term,
                            "channel": ch_id,
                            "mode": "decodo",
                            "action": "harvest_origin_candidates",
                            "query": {
                                "q": f"\"{term}\" earliest mention OR first posted OR originally posted",
                                "domains": domains,
                            },
                            "rationale": miss,
                        }
                    )
                    actions.append(
                        {
                            "term": term,
                            "channel": ch_id,
                            "mode": "decodo",
                            "action": "harvest_template_variants",
                            "query": {
                                "q": f"\"{term}\" \"copy\" OR \"paste\" OR \"template\" OR \"script\"",
                                "domains": domains,
                            },
                            "rationale": miss,
                        }
                    )
                    actions.append(
                        {
                            "term": term,
                            "channel": ch_id,
                            "mode": "decodo",
                            "action": "harvest_counterclaims_primary",
                            "query": {
                                "q": f"\"{term}\" site:.gov OR site:.edu OR filetype:pdf",
                                "domains": domains,
                            },
                            "rationale": miss,
                        }
                    )
                if "ML_LOW_STEERING_RISK" in miss and float(
                    p0.get("consensus_gap_term") or 0.0
                ) >= 0.60:
                    actions.append(
                        {
                            "term": term,
                            "channel": ch_id,
                            "mode": "decodo",
                            "action": "harvest_cross_domain_corroboration",
                            "query": {
                                "q": f"\"{term}\" analysis OR report OR dataset OR timeline",
                                "domains": domains,
                            },
                            "rationale": miss,
                        }
                    )

    out = {
        "version": "acquisition_plan.v0.1",
        "run_id": args.run_id,
        "ts": ts,
        "dmx": {"overall_manipulation_risk": dmx_overall, "bucket": dmx_bucket},
        "decodo": ds,
        "vector_map": vm,
        "ml_index": ml_meta,
        "targets": targets,
        "actions": actions,
        "calibration_tasks": cal_tasks,
        "policy": {
            "online_not_abandoned": True,
            "decodo_primary": True,
            "fallback_behavior": "label_blocked_and_prompt_offline_if_needed",
            "non_truncation": True,
        },
        "provenance": {
            "builder": "abx.acquisition_plan.v0.1",
            "a2_phase": a2_path,
            "mwr": mwr_path,
        },
    }

    path = os.path.join(args.out_reports, f"acquisition_plan_{args.run_id}.json")
    _write_json(path, out)
    print(f"[ACQUISITION_PLAN] wrote: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
