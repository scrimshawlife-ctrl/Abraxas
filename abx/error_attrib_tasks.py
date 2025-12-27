from __future__ import annotations

import argparse
import glob
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = " ".join(s.replace("-", " ").replace("_", " ").split())
    return s


def _latest(out_reports: str, pattern: str) -> str:
    paths = sorted(glob.glob(os.path.join(out_reports, pattern)))
    return paths[-1] if paths else ""


def _pick_recent_run_ids(out_reports: str, n: int = 6) -> List[str]:
    paths = sorted(glob.glob(os.path.join(out_reports, "tpi_*.json")))
    rids = [
        os.path.basename(p).replace("tpi_", "").replace(".json", "") for p in paths
    ]
    return rids[-n:] if len(rids) > n else rids


def generate_tasks(out_reports: str, recent_n: int = 6) -> Dict[str, Any]:
    cal_path = _latest(out_reports, "calibration_report_*.json")
    cal = _read_json(cal_path) if cal_path else {}
    best = cal.get("best") if isinstance(cal.get("best"), dict) else {}

    slang_path = _latest(out_reports, "slang_drift_*.json")
    slang = _read_json(slang_path) if slang_path else {}

    ml_map: Dict[str, Dict[str, Any]] = {}
    terms = slang.get("terms") if isinstance(slang.get("terms"), list) else []
    for it in terms:
        if not isinstance(it, dict):
            continue
        canon = str(it.get("canonical_term") or "").strip()
        if not canon:
            continue
        m = it.get("manufacture") if isinstance(it.get("manufacture"), dict) else {}
        variants = (
            it.get("variants")
            if isinstance(it.get("variants"), list)
            else [canon]
        )
        cell = {
            "canonical": canon,
            "ml": float(m.get("ml_score") or 0.0),
            "bucket": str(m.get("bucket") or "UNKNOWN"),
            "signals": m.get("signals") or [],
        }
        ml_map[_norm(canon)] = cell
        for v in variants:
            ml_map[_norm(str(v))] = cell

    run_ids = _pick_recent_run_ids(out_reports, n=recent_n)
    run_summaries = []
    tasks: List[Dict[str, Any]] = []

    for rid in run_ids:
        tpi_path = os.path.join(out_reports, f"tpi_{rid}.json")
        tpi = _read_json(tpi_path)
        run_tpi = float(tpi.get("run_tpi") or 0.0)

        per = tpi.get("per_term") if isinstance(tpi.get("per_term"), dict) else {}
        items = sorted(
            per.items(),
            key=lambda kv: -float((kv[1] or {}).get("tpi") or 0.0),
        )
        top_terms = []
        for tk, v in items[:12]:
            comp = (
                (v or {}).get("components")
                if isinstance((v or {}).get("components"), dict)
                else {}
            )
            top_terms.append(
                {
                    "term": tk,
                    "tpi": float((v or {}).get("tpi") or 0.0),
                    "components": comp,
                }
            )

        run_summaries.append(
            {"run_id": rid, "run_tpi": run_tpi, "top_terms": top_terms}
        )

        if run_tpi < 0.34:
            continue

        for tt in top_terms[:6]:
            term = str(tt["term"])
            comp = tt.get("components") if isinstance(tt.get("components"), dict) else {}
            syn = float(comp.get("synthetic_density") or 0.0)
            prov = float(comp.get("provenance_integrity_mean") or 0.0)
            tpl = float(comp.get("template_pressure") or 0.0)
            fog = comp.get("fog_flags") if isinstance(comp.get("fog_flags"), dict) else {}

            ml = ml_map.get(
                _norm(term), {"ml": 0.0, "bucket": "UNKNOWN", "signals": []}
            )

            pain = []
            pain.append(("SYN", syn))
            pain.append(("TPL", tpl))
            pain.append(("PROV_GAP", 1.0 - prov))
            fog_p = 0.0
            fog_p += 0.35 if int(fog.get("OP_FOG", 0)) > 0 else 0.0
            fog_p += 0.30 if int(fog.get("FORK_STORM", 0)) > 0 else 0.0
            fog_p += 0.30 if int(fog.get("PROVENANCE_DROUGHT", 0)) > 0 else 0.0
            pain.append(("FOG", fog_p))
            pain.sort(key=lambda x: -x[1])
            dom = pain[0][0]

            base = {
                "run_id": rid,
                "term": term,
                "term_tpi": float(tt.get("tpi") or 0.0),
                "ml": ml,
                "dominant_driver": dom,
                "components": {"syn": syn, "prov": prov, "tpl": tpl, "fog": fog},
                "notes": (
                    "Tasks are evidence-acquisition directives to reduce forecast error "
                    "and pollution uncertainty."
                ),
            }

            if dom == "PROV_GAP" or dom == "FOG":
                tasks.append(
                    {
                        **base,
                        "task_type": "PRIMARY_ANCHOR_SWEEP",
                        "mode": "online_or_offline",
                        "instruction": (
                            f"Collect 3 primary-source anchors for '{term}' "
                            "(official docs/filings/transcripts). Include date + claim mapping. "
                            "Tag: primary,official."
                        ),
                        "tags": ["primary", "official", "provenance"],
                    }
                )
                tasks.append(
                    {
                        **base,
                        "task_type": "ORIGIN_TIMELINE",
                        "mode": "online_or_offline",
                        "instruction": (
                            f"Build an origin timeline for '{term}': earliest appearance, "
                            "first 3 upstream references, and when it jumped communities. "
                            "Tag: timeline,origin."
                        ),
                        "tags": ["timeline", "origin"],
                    }
                )

            if dom == "TPL" or float(ml.get("ml") or 0.0) >= 0.67:
                tasks.append(
                    {
                        **base,
                        "task_type": "TEMPLATE_CAPTURE",
                        "mode": "manual_offline",
                        "instruction": (
                            f"For '{term}', capture 5 examples with near-identical phrasing "
                            "+ timestamps + account metadata (if available). "
                            "Tag: template,copy,paste."
                        ),
                        "tags": ["template", "copy", "paste"],
                    }
                )
                tasks.append(
                    {
                        **base,
                        "task_type": "SYNC_POSTING_CHECK",
                        "mode": "manual_offline",
                        "instruction": (
                            f"Check synchronized posting for '{term}': do clusters post within "
                            "tight windows? Provide 10 timestamps if possible. "
                            "Tag: bot,coordination (label-only)."
                        ),
                        "tags": ["bot", "coordination"],
                    }
                )

            if dom == "SYN":
                tasks.append(
                    {
                        **base,
                        "task_type": "AUTH_CHAIN",
                        "mode": "online_or_offline",
                        "instruction": (
                            f"For '{term}', gather provenance chain: original media file if possible, "
                            "repost trail, and any official source confirming/denying. "
                            "Tag: authenticity,chain."
                        ),
                        "tags": ["authenticity", "chain"],
                    }
                )
                tasks.append(
                    {
                        **base,
                        "task_type": "DISCONFIRM_TESTS",
                        "mode": "manual_offline",
                        "instruction": (
                            f"Write 2 disconfirming tests for the strongest claim attached to '{term}'. "
                            "Tag: falsification,test."
                        ),
                        "tags": ["falsification", "test"],
                    }
                )

    return {
        "version": "calibration_tasks.v0.1",
        "ts": _utc_now_iso(),
        "out_reports": out_reports,
        "calibration_report": cal_path,
        "slang_drift": slang_path,
        "best_params": best,
        "recent_runs": run_summaries,
        "tasks": tasks,
        "notes": (
            "Tasks are emitted only when recent runs show elevated pollution; "
            "no censorship, only directed acquisition."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Generate calibration-driven evidence tasks from recent TPI + slang drift ML"
    )
    ap.add_argument("--out-reports", default="out/reports")
    ap.add_argument("--recent-n", type=int, default=6)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    obj = generate_tasks(args.out_reports, int(args.recent_n))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join(
        args.out_reports, f"calibration_tasks_{stamp}.json"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[CAL_TASKS] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
