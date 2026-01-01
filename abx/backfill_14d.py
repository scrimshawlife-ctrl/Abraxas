from __future__ import annotations

import argparse
import glob
import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


_RUN_RE = re.compile(r".*_(\d{8}T\d{2,6}|\d{8})\.json$")


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


def _write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _extract_run_id(path: str) -> Optional[str]:
    match = _RUN_RE.match(path)
    return match.group(1) if match else None


def _parse_run_time(run_id: str) -> Optional[datetime]:
    if not run_id:
        return None
    try:
        if "T" in run_id:
            date, time = run_id.split("T", 1)
            if len(time) == 2:
                time = time + "0000"
            elif len(time) == 4:
                time = time + "00"
            return datetime.strptime(date + time, "%Y%m%d%H%M%S").replace(
                tzinfo=timezone.utc
            )
        return datetime.strptime(run_id, "%Y%m%d").replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _list_runs(out_reports: str) -> List[Dict[str, Any]]:
    paths = sorted(glob.glob(os.path.join(out_reports, "a2_phase_*.json")))
    runs = []
    for path in paths:
        run_id = _extract_run_id(path) or path.split("a2_phase_", 1)[-1].replace(
            ".json", ""
        )
        dt = _parse_run_time(run_id)
        mtime = os.path.getmtime(path)
        runs.append({"run_id": run_id, "a2_path": path, "dt": dt, "mtime": mtime})
    runs.sort(
        key=lambda r: (
            r["dt"] is None,
            r["dt"] or datetime.fromtimestamp(r["mtime"], tz=timezone.utc),
            r["run_id"],
        )
    )
    return runs


def _within_days(run: Dict[str, Any], days: int, now: datetime) -> bool:
    dt = run.get("dt")
    if isinstance(dt, datetime):
        return dt >= (now - timedelta(days=days))
    mtime = float(run.get("mtime") or 0.0)
    dt2 = datetime.fromtimestamp(mtime, tz=timezone.utc)
    return dt2 >= (now - timedelta(days=days))


def _profiles(a2: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = a2.get("raw_full") if isinstance(a2, dict) else {}
    profs = raw.get("profiles") if isinstance(raw, dict) else None
    if isinstance(profs, list):
        return [p for p in profs if isinstance(p, dict)]
    views = (a2.get("views") or {}).get("profiles_top") if isinstance(a2, dict) else None
    if isinstance(views, list):
        return [p for p in views if isinstance(p, dict)]
    return []


def _term_key(term: str) -> str:
    return (term or "").strip().lower()


def _get_term_score(profile: Dict[str, Any]) -> float:
    mr = float(profile.get("manipulation_risk") or 0.0)
    cg = float(profile.get("consensus_gap_term") or 0.0)
    att = float(
        profile.get("attribution_strength_uplifted")
        or profile.get("attribution_strength")
        or 0.0
    )
    sd = float(
        profile.get("source_diversity_uplifted")
        or profile.get("source_diversity")
        or 0.0
    )
    return (1.0 * mr) + (0.9 * cg) + (0.7 * (1.0 - att)) + (0.5 * (1.0 - sd))


def _collect_terms(profiles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for profile in profiles:
        term = str(profile.get("term") or "").strip()
        if not term:
            continue
        csp = (
            profile.get("term_csp_summary")
            if isinstance(profile.get("term_csp_summary"), dict)
            else {}
        )
        out.append(
            {
                "term": term,
                "score": _get_term_score(profile),
                "mr": float(profile.get("manipulation_risk") or 0.0),
                "cg": float(profile.get("consensus_gap_term") or 0.0),
                "att": float(
                    profile.get("attribution_strength_uplifted")
                    or profile.get("attribution_strength")
                    or 0.0
                ),
                "sd": float(
                    profile.get("source_diversity_uplifted")
                    or profile.get("source_diversity")
                    or 0.0
                ),
                "csp": (
                    {
                        "COH": bool(csp.get("COH")),
                        "tag": str(csp.get("tag") or "unknown"),
                        "EA": float(csp.get("EA") or 0.0),
                        "FF": float(csp.get("FF") or 0.0),
                        "MIO": float(csp.get("MIO") or 0.0),
                        "CIP": float(csp.get("CIP") or 0.0),
                    }
                    if csp
                    else {}
                ),
            }
        )
    out.sort(key=lambda x: (-float(x["score"]), x["term"].lower()))
    return out


def _rollup_mwr(mwr: Dict[str, Any], enriched: Dict[str, Any]) -> Dict[str, Any]:
    dmx = mwr.get("dmx") if isinstance(mwr.get("dmx"), dict) else {}
    bucket = str(dmx.get("bucket") or "UNKNOWN").upper()
    overall = float(dmx.get("overall_manipulation_risk") or 0.0)

    fog_counts: Dict[str, int] = {}
    cw = (
        enriched.get("csp_weather")
        if isinstance(enriched.get("csp_weather"), dict)
        else {}
    )
    fc = cw.get("fog_counts") if isinstance(cw.get("fog_counts"), dict) else {}
    for key, value in fc.items():
        fog_counts[str(key)] = int(value)

    return {"dmx_bucket": bucket, "dmx_overall": overall, "fog_counts": fog_counts}


def _md_header(stamp: str, days: int, runs: List[Dict[str, Any]]) -> str:
    return (
        f"# AAlmanac Backfill ({days}d)\n\n"
        f"- stamp: `{stamp}`\n"
        f"- ts: `{_utc_now_iso()}`\n"
        f"- runs_processed: `{len(runs)}`\n\n"
    )


def main() -> int:
    p = argparse.ArgumentParser(
        description="Backfill last N days into AAlmanac + slang + mimetic rollups"
    )
    p.add_argument("--days", type=int, default=14)
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument("--max-terms-per-run", type=int, default=25)
    args = p.parse_args()

    now = _utc_now()
    stamp = now.strftime("%Y%m%dT%H%M%SZ")

    runs_all = _list_runs(args.out_reports)
    runs = [r for r in runs_all if _within_days(r, args.days, now)]

    backfill_index: Dict[str, Any] = {
        "version": "backfill_index.v0.1",
        "stamp": stamp,
        "ts": _utc_now_iso(),
        "days": args.days,
        "runs": [],
        "notes": (
            "Anchored on a2_phase_*.json. Deterministic sort. "
            "Window by run dt or file mtime."
        ),
    }

    slang_terms: Dict[str, Dict[str, Any]] = {}
    mwr_roll: Dict[str, Any] = {
        "dmx_bucket_counts": {},
        "dmx_overall_mean": 0.0,
        "fog_counts": {},
    }
    dmx_overall_sum = 0.0
    dmx_overall_n = 0
    tpi_sum = 0.0
    tpi_n = 0

    md = _md_header(stamp, args.days, runs)

    for run in runs:
        run_id = run["run_id"]
        a2 = _read_json(run["a2_path"])
        mwr = _read_json(os.path.join(args.out_reports, f"mwr_{run_id}.json"))
        mwr_en = _read_json(
            os.path.join(args.out_reports, f"mwr_enriched_{run_id}.json")
        )

        profiles = _profiles(a2)
        terms = _collect_terms(profiles)[: int(args.max_terms_per_run)]

        dmx = mwr.get("dmx") if isinstance(mwr.get("dmx"), dict) else {}
        dmx_bucket = str(dmx.get("bucket") or "UNKNOWN").upper()
        dmx_overall = float(dmx.get("overall_manipulation_risk") or 0.0)
        tpi_value = None
        tpi_path = os.path.join(args.out_reports, f"tpi_{run_id}.json")
        if os.path.exists(tpi_path):
            tpi_obj = _read_json(tpi_path)
            if isinstance(tpi_obj, dict):
                tpi_value = float(tpi_obj.get("run_tpi") or 0.0)

        backfill_index["runs"].append(
            {
                "run_id": run_id,
                "a2_path": run["a2_path"],
                "mwr_path": os.path.join(args.out_reports, f"mwr_{run_id}.json"),
                "mwr_enriched_path": os.path.join(
                    args.out_reports, f"mwr_enriched_{run_id}.json"
                ),
                "dmx_bucket": dmx_bucket,
                "dmx_overall": dmx_overall,
                "tpi": tpi_value if tpi_value is not None else None,
                "top_terms": [t["term"] for t in terms[:10]],
            }
        )

        mwr_roll["dmx_bucket_counts"][dmx_bucket] = int(
            mwr_roll["dmx_bucket_counts"].get(dmx_bucket, 0)
        ) + 1
        dmx_overall_sum += dmx_overall
        dmx_overall_n += 1
        if tpi_value is not None:
            tpi_sum += float(tpi_value)
            tpi_n += 1

        rr = _rollup_mwr(mwr, mwr_en)
        for key, value in rr.get("fog_counts", {}).items():
            mwr_roll["fog_counts"][key] = int(
                mwr_roll["fog_counts"].get(key, 0)
            ) + int(value)

        for term_entry in terms:
            term_key = _term_key(term_entry["term"])
            cell = slang_terms.setdefault(
                term_key,
                {
                    "term": term_entry["term"],
                    "appearances": 0,
                    "max_score": 0.0,
                    "last_run": "",
                    "csp_tags": {},
                    "mr_max": 0.0,
                },
            )
            cell["appearances"] += 1
            cell["max_score"] = max(float(cell["max_score"]), float(term_entry["score"]))
            cell["last_run"] = run_id
            cell["mr_max"] = max(float(cell["mr_max"]), float(term_entry["mr"]))
            tag = str((term_entry.get("csp") or {}).get("tag") or "unknown")
            cell["csp_tags"][tag] = int(cell["csp_tags"].get(tag, 0)) + 1

        md += f"## Run `{run_id}`\n\n"
        tpi_line = (
            f"- TPI: {tpi_value:.3f}\n" if isinstance(tpi_value, float) else "- TPI: n/a\n"
        )
        md += f"- DMX: bucket={dmx_bucket} overall={dmx_overall:.3f}\n{tpi_line}\n"
        md += "| term | score | mr | cg | att | sd | CSP(tag/EA/FF/MIO) |\n"
        md += "|---|---:|---:|---:|---:|---:|---|\n"
        for term_entry in terms[:15]:
            csp = term_entry.get("csp") or {}
            md += (
                f"| {term_entry['term']} | {term_entry['score']:.3f} | "
                f"{term_entry['mr']:.3f} | {term_entry['cg']:.3f} | "
                f"{term_entry['att']:.3f} | {term_entry['sd']:.3f} | "
                f"{csp.get('tag','')} / EA={csp.get('EA',0.0):.2f} "
                f"FF={csp.get('FF',0.0):.2f} MIO={csp.get('MIO',0.0):.2f} |\n"
            )
        md += "\n"

    mwr_roll["dmx_overall_mean"] = (
        dmx_overall_sum / dmx_overall_n if dmx_overall_n else 0.0
    )
    mwr_roll["tpi_mean"] = tpi_sum / tpi_n if tpi_n else 0.0

    try:
        from abx.slang_drift import run_slang_drift

        slang_out = run_slang_drift(
            out_reports=args.out_reports,
            days=args.days,
            baseline_lexicon_path=None,
            per_run_terms_limit=200,
            cooc_window_k=25,
        )
    except Exception as e:
        slang_out = {
            "version": "slang_drift.v0.2",
            "stamp": stamp,
            "ts": _utc_now_iso(),
            "days": args.days,
            "count": 0,
            "terms": [],
            "notes": f"slang_drift import failed: {e}",
        }

    idx_path = os.path.join(args.out_reports, f"backfill_index_{stamp}.json")
    md_path = os.path.join(args.out_reports, f"AAlmanac_{stamp}.md")
    slang_path = os.path.join(args.out_reports, f"slang_drift_{stamp}.json")
    mwr_path = os.path.join(args.out_reports, f"mimetic_weather_rollup_{stamp}.json")

    _write_json(idx_path, backfill_index)
    _write_text(md_path, md)
    _write_json(slang_path, slang_out)

    try:
        top = slang_out.get("terms") if isinstance(slang_out, dict) else []
        if isinstance(top, list) and top:
            md_add = "## Slang Drift Digest (v0.2)\n\n"
            md_add += "| canonical | new-to-window | drift | appearances | fog tags |\n"
            md_add += "|---|---:|---:|---:|---|\n"
            for it in top[:20]:
                if not isinstance(it, dict):
                    continue
                canon = str(it.get("canonical_term") or "")
                n2w = 1 if (it.get("novelty") or {}).get("new_to_window") else 0
                drift = float((it.get("drift") or {}).get("drift_score") or 0.0)
                app = int(it.get("appearances") or 0)
                fog = (
                    it.get("fog_type_counts")
                    if isinstance(it.get("fog_type_counts"), dict)
                    else {}
                )
                fog_keys = ",".join(sorted(fog.keys())) if fog else ""
                md_add += f"| {canon} | {n2w} | {drift:.3f} | {app} | {fog_keys} |\n"
            md_add += "\n"

            md_add += "## Manufacture Risk Digest (v0.1)\n\n"
            md_add += "| canonical | ML | bucket | top signals |\n"
            md_add += "|---|---:|---|---|\n"
            for it in top[:25]:
                if not isinstance(it, dict):
                    continue
                canon = str(it.get("canonical_term") or "")
                m = it.get("manufacture") if isinstance(it.get("manufacture"), dict) else {}
                ml = float(m.get("ml_score") or 0.0)
                bucket = str(m.get("bucket") or "UNKNOWN")
                sig = m.get("signals") if isinstance(m.get("signals"), list) else []
                sigs = ", ".join([str(x) for x in sig[:5]])
                md_add += f"| {canon} | {ml:.3f} | {bucket} | {sigs} |\n"
            md_add += "\n"

            try:
                with open(md_path, "a", encoding="utf-8") as f:
                    f.write(md_add)
            except Exception:
                pass
    except Exception:
        pass
    try:
        if runs:
            last_run = runs[-1]["run_id"]
            en_path = os.path.join(args.out_reports, f"mwr_enriched_{last_run}.json")
            en = _read_json(en_path)
            po = (
                en.get("pollution_outlook")
                if isinstance(en.get("pollution_outlook"), dict)
                else {}
            )
            scenarios = po.get("scenarios") if isinstance(po.get("scenarios"), list) else []
            if scenarios:
                md_add = "## Pollution Outlook (TPI) — 30d Scenarios\n\n"
                md_add += "| scenario | end_30d | key alerts |\n"
                md_add += "|---|---:|---|\n"
                for s in scenarios:
                    if not isinstance(s, dict):
                        continue
                    name = str(s.get("scenario") or "")
                    endv = float(s.get("end_30d") or 0.0)
                    alerts = s.get("alerts") if isinstance(s.get("alerts"), list) else []
                    alert_bits = []
                    for a in alerts[:3]:
                        if not isinstance(a, dict):
                            continue
                        alert_bits.append(
                            f"{a.get('type')}@d{a.get('day')}"
                        )
                    md_add += f"| {name} | {endv:.3f} | {'; '.join(alert_bits)} |\n"
                md_add += "\n"
                try:
                    with open(md_path, "a", encoding="utf-8") as f:
                        f.write(md_add)
                except Exception:
                    pass
    except Exception:
        pass
    _write_json(
        mwr_path,
        {
            "version": "mimetic_weather_rollup.v0.1",
            "stamp": stamp,
            "ts": _utc_now_iso(),
            "days": args.days,
            "rollup": mwr_roll,
            "notes": (
                "Aggregated DMX buckets/means and CSP fog type counts from "
                "mwr_enriched if present. Includes mean TPI when available."
            ),
        },
    )

    print(f"[BACKFILL] wrote: {idx_path}")
    print(f"[BACKFILL] wrote: {md_path}")
    print(f"[BACKFILL] wrote: {slang_path}")
    print(f"[BACKFILL] wrote: {mwr_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
