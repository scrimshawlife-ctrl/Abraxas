from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from abraxas_ase.anomaly import build_anomalies
from abraxas_ase.chronoscope import ChronoscopeState, DayPoint, load_state, update_state, write_state
from abraxas_ase.leakage_linter import lint_report_for_tier
from abraxas_ase.provenance import stable_json_dumps
from abraxas_ase.watchlist import WatchlistRule, WatchlistState, default_state, evaluate_watchlist


def _read_csv(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def _read_pack(pack_dir: Path) -> Dict[str, Any]:
    index_path = pack_dir / "index.json"
    if index_path.exists():
        return json.loads(index_path.read_text(encoding="utf-8"))
    report_path = pack_dir / "daily_report.json"
    if report_path.exists():
        return json.loads(report_path.read_text(encoding="utf-8"))
    raise SystemExit(f"No index.json or daily_report.json found in {pack_dir}")


def _daypoint_from_pack(pack_dir: Path, data: Dict[str, Any]) -> DayPoint:
    manifest_path = pack_dir / "manifest.json"
    pack_hash = None
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        pack_hash = manifest.get("manifest_sha256")

    top_tap = _read_csv(pack_dir / "tables" / "tap_top.csv")
    top_sas = _read_csv(pack_dir / "tables" / "sas.csv")

    return DayPoint(
        date=str(data.get("date", "")),
        run_id=data.get("run_id"),
        counts=dict(data.get("counts", data.get("stats", {}))),
        top_tap=top_tap,
        top_sas=top_sas,
        lane_counts={k: int(v) for k, v in dict(data.get("lane_counts", {})).items()},
        pfdi_alerts_count=int(data.get("alerts", {}).get("pfdi", data.get("pfdi_alerts_count", 0))),
        pack_hash=pack_hash,
    )


def _daypoint_from_report(report: Dict[str, Any]) -> DayPoint:
    return DayPoint(
        date=str(report.get("date", "")),
        run_id=report.get("run_id"),
        counts=dict(report.get("stats", {})),
        top_tap=list(report.get("high_tap_tokens", [])),
        top_sas=list(report.get("sas", {}).get("rows", [])),
        lane_counts={
            "core": sum(1 for h in report.get("verified_sub_anagrams", []) if h.get("lane") == "core"),
            "canary": sum(1 for h in report.get("verified_sub_anagrams", []) if h.get("lane") == "canary"),
        },
        pfdi_alerts_count=len(report.get("pfdi_alerts", [])),
        pack_hash=None,
    )


def _build_metrics(state: ChronoscopeState) -> Dict[str, List[Tuple[str, float]]]:
    metrics: Dict[str, List[Tuple[str, float]]] = {
        "pfdi_alerts": [],
        "tier2_hits": [],
        "lane_core": [],
        "lane_canary": [],
    }
    for dp in state.series:
        metrics["pfdi_alerts"].append((dp.date, float(dp.pfdi_alerts_count)))
        metrics["tier2_hits"].append((dp.date, float(dp.counts.get("tier2_hits", 0))))
        metrics["lane_core"].append((dp.date, float(dp.lane_counts.get("core", 0))))
        metrics["lane_canary"].append((dp.date, float(dp.lane_counts.get("canary", 0))))
    return metrics


def _load_rules(path: Path) -> List[WatchlistRule]:
    if not path.exists():
        raise SystemExit(f"Watchlist rules file not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    rules = []
    for item in raw.get("rules", []):
        rules.append(WatchlistRule(
            id=str(item.get("id")),
            label=str(item.get("label")),
            kind=str(item.get("kind")),
            target=str(item.get("target")),
            metric=str(item.get("metric")),
            trigger_delta=float(item.get("trigger_delta", 0.0)),
            trigger_score=float(item.get("trigger_score", 0.0)),
            decay_halflife_days=int(item.get("decay_halflife_days", 1)),
            min_days_seen=int(item.get("min_days_seen", 1)),
        ))
    return rules


def _tier_filter_chronoscope(
    tier: str,
    state: ChronoscopeState,
    anomalies: List[Dict[str, Any]],
    triggers: List[Dict[str, Any]],
) -> Dict[str, Any]:
    tier_norm = (tier or "psychonaut").lower()
    series = [asdict(dp) for dp in state.series]

    if tier_norm == "psychonaut":
        trimmed = []
        for dp in series[-7:]:
            trimmed.append({
                "date": dp.get("date"),
                "counts": dp.get("counts"),
                "pfdi_alerts_count": dp.get("pfdi_alerts_count"),
            })
        return {
            "tier": tier_norm,
            "series": trimmed,
            "anomalies": anomalies[:3],
        }

    if tier_norm == "academic":
        trimmed = []
        for dp in series:
            trimmed.append({
                "date": dp.get("date"),
                "run_id": dp.get("run_id"),
                "counts": dp.get("counts"),
                "pfdi_alerts_count": dp.get("pfdi_alerts_count"),
                "lane_counts": dp.get("lane_counts"),
                "top_tap": dp.get("top_tap", [])[:10],
                "top_sas": dp.get("top_sas", [])[:10],
            })
        return {
            "tier": tier_norm,
            "series": trimmed,
            "anomalies": anomalies[:25],
        }

    return {
        "tier": tier_norm,
        "series": series,
        "anomalies": anomalies,
        "watchlist_triggers": triggers,
    }


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m abraxas_ase.tools.chronoscope_update")
    ap.add_argument("--state", required=True, help="Path to chronoscope_state.json")
    ap.add_argument("--input", required=True, help="Path to pack dir or daily_report.json")
    ap.add_argument("--tier", required=True, choices=["psychonaut", "academic", "enterprise"])
    ap.add_argument("--rules", default="", help="Path to watchlist rules (enterprise only)")
    ap.add_argument("--outdir", required=True, help="Output directory for chronoscope outputs")
    ap.add_argument("--window", type=int, default=14, help="Window size for anomaly scoring")
    args = ap.parse_args()

    input_path = Path(args.input)
    tier_norm = args.tier.lower()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    key_fp = None
    if input_path.is_dir():
        data = _read_pack(input_path)
        day_point = _daypoint_from_pack(input_path, data)
        key_fp = data.get("key_fingerprint")
    else:
        report = json.loads(input_path.read_text(encoding="utf-8"))
        violations = lint_report_for_tier(report, tier=tier_norm)
        if violations:
            msg = "\n".join(violations)
            raise SystemExit(f"Chronoscope input blocked due to tier leakage:\n{msg}")
        day_point = _daypoint_from_report(report)
        key_fp = report.get("key_fingerprint")

    state_path = Path(args.state)
    state = load_state(state_path)
    key_fp = state.key_fingerprint or key_fp
    state = ChronoscopeState(version=state.version, key_fingerprint=key_fp, series=state.series)
    state = update_state(state, day_point)
    write_state(outdir / "chronoscope_state.json", state)

    metrics = _build_metrics(state)
    anomalies = build_anomalies(metrics, window=args.window)

    triggers = []
    watch_state = default_state()
    if tier_norm == "enterprise" and args.rules:
        rules = _load_rules(Path(args.rules))
        history = [asdict(dp) for dp in state.series[:-1]]
        triggers, watch_state = evaluate_watchlist(asdict(state.series[-1]), history, rules, watch_state)
        (outdir / "watchlist_triggers.json").write_text(
            stable_json_dumps({"triggers": triggers, "state": watch_state.__dict__}) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    filtered = _tier_filter_chronoscope(tier_norm, state, anomalies, triggers)
    (outdir / "chronoscope_report.json").write_text(stable_json_dumps(filtered) + "\n", encoding="utf-8", newline="\n")
    (outdir / "anomalies.json").write_text(stable_json_dumps({"anomalies": anomalies}) + "\n", encoding="utf-8", newline="\n")

    print(stable_json_dumps({"status": "ok", "outdir": str(outdir)}))


if __name__ == "__main__":
    main()
