from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from abx.truth_pollution import compute_tpi_for_run
from abx.tpi_forecast import forecast_tpi, compute_alerts

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _profiles(a2: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = a2.get("raw_full") if isinstance(a2, dict) else {}
    profiles = raw.get("profiles") if isinstance(raw, dict) else None
    if isinstance(profiles, list):
        return [p for p in profiles if isinstance(p, dict)]
    views = (a2.get("views") or {}).get("profiles_top") if isinstance(a2, dict) else None
    if isinstance(views, list):
        return [p for p in views if isinstance(p, dict)]
    return []


def fog_types_from_csp(profile: Dict[str, Any], dmx_bucket: str) -> List[str]:
    out: List[str] = []
    csp = (
        profile.get("term_csp_summary")
        if isinstance(profile.get("term_csp_summary"), dict)
        else {}
    )
    if not csp:
        return out

    coh = bool(csp.get("COH"))
    tag = str(csp.get("tag") or "unknown")
    mio = float(csp.get("MIO") or 0.0)
    ea = float(csp.get("EA") or 0.0)
    ff = float(csp.get("FF") or 0.0)

    if tag == "investigative":
        out.append("INVESTIGATIVE_CORRIDOR")
    if tag == "plausible_unproven":
        out.append("PLAUSIBLE_UNPROVEN_TENSION")
    if tag == "speculative":
        out.append("SPECULATIVE_HAZE")
    if tag == "opportunistic_op":
        out.append("OP_FOG")
    if tag == "noise_halo":
        out.append("NOISE_HALO")

    if (dmx_bucket or "UNKNOWN").upper() == "HIGH" and mio >= 0.70 and ea < 0.50:
        out.append("PROVENANCE_DROUGHT")
    if mio >= 0.75 and ff <= 0.45:
        out.append("FORK_STORM")
    if coh and ea >= 0.60 and ff >= 0.60:
        out.append("COH_HIGH_EQ")

    seen = set()
    unique = []
    for item in out:
        if item not in seen:
            unique.append(item)
            seen.add(item)
    return unique


def main() -> int:
    p = argparse.ArgumentParser(description="Enrich Mimetic Weather with CSP regimes")
    p.add_argument("--run-id", required=True)
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument("--ledger", default="out/ledger/evidence_ledger.jsonl")
    args = p.parse_args()

    ts = _utc_now_iso()
    mwr_path = os.path.join(args.out_reports, f"mwr_{args.run_id}.json")
    a2_path = os.path.join(args.out_reports, f"a2_phase_{args.run_id}.json")

    mwr = _read_json(mwr_path)
    a2 = _read_json(a2_path)

    dmx = mwr.get("dmx") if isinstance(mwr.get("dmx"), dict) else {}
    dmx_bucket = str(dmx.get("bucket") or "UNKNOWN").upper()

    fog_index: Dict[str, Any] = {
        "run_id": args.run_id,
        "ts": ts,
        "dmx_bucket": dmx_bucket,
        "by_term": {},
    }
    fog_counts: Dict[str, int] = {}

    for profile in _profiles(a2):
        term = str(profile.get("term") or "").strip()
        if not term:
            continue
        tags = fog_types_from_csp(profile, dmx_bucket)
        if not tags:
            continue
        fog_index["by_term"][term] = tags
        for tag in tags:
            fog_counts[tag] = int(fog_counts.get(tag, 0)) + 1

    enriched = dict(mwr)
    enriched["csp_weather"] = {
        "fog_counts": fog_counts,
        "fog_index": fog_index,
        "notes": "CSP-derived symbolic regimes (label-only).",
    }
    provenance = (
        enriched.get("provenance") if isinstance(enriched.get("provenance"), dict) else {}
    )
    provenance["mwr_enrich"] = {"builder": "abx.mwr_enrich.v0.1", "ts": ts}
    enriched["provenance"] = provenance

    out_path = os.path.join(args.out_reports, f"mwr_enriched_{args.run_id}.json")
    _write_json(out_path, enriched)
    try:
        tpi = compute_tpi_for_run(
            run_id=args.run_id,
            out_reports=args.out_reports,
            ledger_path=args.ledger,
            mwr_enriched_path=out_path,
        )
        enriched["tpi"] = {
            "run_tpi": float(tpi.get("run_tpi") or 0.0),
            "fog_roll": tpi.get("fog_roll") or {},
            "notes": "TPI computed post-enrich using fog regimes.",
        }
        dmx_adjunct = (
            enriched.get("dmx_adjunct")
            if isinstance(enriched.get("dmx_adjunct"), dict)
            else {}
        )
        dmx_adjunct["tpi"] = float(tpi.get("run_tpi") or 0.0)
        enriched["dmx_adjunct"] = dmx_adjunct
        per_term = tpi.get("per_term") if isinstance(tpi.get("per_term"), dict) else {}
        items = sorted(
            per_term.items(),
            key=lambda kv: -float((kv[1] or {}).get("tpi") or 0.0),
        )
        enriched["tpi_by_term_top"] = [
            {"term": k, "tpi": float((v or {}).get("tpi") or 0.0)}
            for k, v in items[:50]
        ]
        try:
            tpi_now = float((enriched.get("tpi") or {}).get("run_tpi") or 0.0)
            fog_roll = (
                (enriched.get("tpi") or {}).get("fog_roll")
                if isinstance((enriched.get("tpi") or {}).get("fog_roll"), dict)
                else {}
            )
            slang_obj = {}
            try:
                import glob

                paths = sorted(
                    glob.glob(os.path.join(args.out_reports, "slang_drift_*.json"))
                )
                if paths:
                    with open(paths[-1], "r", encoding="utf-8") as f:
                        slang_obj = json.load(f)
            except Exception:
                slang_obj = {}

            scen = [
                ("BALANCED", 0.55, 0.55, 21.0),
                ("AGGRESSIVE", 0.70, 0.45, 30.0),
                ("RECOVERY", 0.40, 0.75, 10.0),
            ]
            outs = []
            for name, mri, iri, tau_h in scen:
                f = forecast_tpi(
                    tpi_now=tpi_now,
                    fog_roll=fog_roll or {},
                    slang_drift_obj=slang_obj if isinstance(slang_obj, dict) else {},
                    horizon_days=30,
                    mri=mri,
                    iri=iri,
                    tau_half_life_days=tau_h,
                    scenario_name=name,
                )
                f["alerts"] = compute_alerts(f["series"])
                outs.append(
                    {
                        "scenario": name,
                        "end_30d": float(f.get("end") or 0.0),
                        "alerts": (f.get("alerts") or [])[:5],
                        "params": f.get("params") or {},
                    }
                )
            enriched["pollution_outlook"] = {
                "horizon_days": 30,
                "scenarios": outs,
                "notes": "Scenario-based TPI outlook (conditions forecast). Not truth prediction.",
            }
        except Exception:
            pass
        _write_json(out_path, enriched)
    except Exception:
        pass
    print(f"[MWR_ENRICH] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
