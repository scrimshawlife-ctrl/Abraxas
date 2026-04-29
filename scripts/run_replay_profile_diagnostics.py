from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping

from scripts.run_multi_cycle_replay import _classify_stability
from scripts.run_replay_cycle import run_replay_cycle

PROFILE_IDS = [
    "BASELINE_CURRENT",
    "NO_FLIP",
    "LOW_DRIFT",
    "HIGH_DRIFT",
    "FLIP_ONLY",
    "DOMAIN_ROTATION",
]


def _clamp_probability(value: float) -> float:
    return min(max(value, 0.01), 0.99)


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _profile_payload(base_payload: Mapping[str, Any], profile_id: str, cycle_index: int) -> Dict[str, Any]:
    payload = json.loads(json.dumps(base_payload))
    records = payload.get("records", []) if isinstance(payload.get("records", []), list) else []

    if profile_id in {"BASELINE_CURRENT", "NO_FLIP", "DOMAIN_ROTATION"}:
        offset = (cycle_index % 5) * 0.02
    elif profile_id == "LOW_DRIFT":
        offset = (cycle_index % 5) * 0.01
    elif profile_id == "HIGH_DRIFT":
        offset = (cycle_index % 5) * 0.04
    elif profile_id == "FLIP_ONLY":
        offset = 0.0
    else:
        offset = 0.0

    enable_flip = profile_id in {"FLIP_ONLY"}
    out_records: List[Dict[str, Any]] = []
    flip_idx = cycle_index % len(records) if records else -1

    for idx, rec in enumerate(records):
        row = dict(rec) if isinstance(rec, dict) else {}
        raw_p = row.get("forecast_probability", row.get("probability"))
        try:
            row["forecast_probability"] = _clamp_probability(float(raw_p) + offset)
        except (TypeError, ValueError):
            pass

        if enable_flip and idx == flip_idx:
            outcome = str(row.get("outcome", ""))
            if outcome == "YES":
                row["outcome"] = "NO"
            elif outcome == "NO":
                row["outcome"] = "YES"
        out_records.append(row)

    if profile_id == "DOMAIN_ROTATION" and out_records:
        shift = cycle_index % len(out_records)
        rotated = out_records[shift:] + out_records[:shift]
        domains = sorted(str(r.get("domain", "")) for r in rotated)
        for i, row in enumerate(rotated):
            row["domain"] = domains[i % len(domains)]
        out_records = rotated

    out_records = sorted(out_records, key=lambda r: str(r.get("domain", "")))
    payload["records"] = out_records
    payload["run_id"] = f"diag_{profile_id.lower()}_{cycle_index:03d}"
    return payload


def _run_profile(base_payload: Mapping[str, Any], profile_id: str, cycles: int, temp_dir: Path) -> Dict[str, Any]:
    series: List[Dict[str, Any]] = []
    outcome_flip_enabled = profile_id == "FLIP_ONLY"
    for i in range(cycles):
        payload = _profile_payload(base_payload, profile_id, i)
        p = temp_dir / f"diag_{profile_id.lower()}_{i:03d}.json"
        p.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        receipt = run_replay_cycle(p.as_posix())
        cal = receipt.get("calibration", {}) if isinstance(receipt.get("calibration", {}), dict) else {}
        fus = receipt.get("fusion", {}) if isinstance(receipt.get("fusion", {}), dict) else {}
        q = receipt.get("operator_queue", {}) if isinstance(receipt.get("operator_queue", {}), dict) else {}
        series.append(
            {
                "mean_brier": float(cal.get("mean_brier", 0.0) or 0.0),
                "confidence": float(fus.get("confidence", 0.0) or 0.0),
                "p0_count": int(q.get("p0_count", 0) or 0),
                "dominance_ratio": float(fus.get("dominance_ratio", 0.0) or 0.0),
                "cycle_status": str(receipt.get("cycle_status", "NOT_COMPUTABLE")),
                "execution_triggered": bool(receipt.get("execution_triggered", False)),
                "runtime_mutation": bool(receipt.get("runtime_mutation", False)),
                "authority_leak_detected": bool(receipt.get("authority_leak_detected", False)),
            }
        )

    n = len(series)
    summary = {
        "outcome_flip_enabled": outcome_flip_enabled,
        "cycle_count": n,
        "pass_count": sum(1 for x in series if x["cycle_status"] == "PASS"),
        "review_required_count": sum(1 for x in series if x["cycle_status"] == "REVIEW_REQUIRED"),
        "blocked_count": sum(1 for x in series if x["cycle_status"] == "BLOCKED"),
        "avg_brier": (sum(x["mean_brier"] for x in series) / n) if n else 0.0,
        "avg_confidence": (sum(x["confidence"] for x in series) / n) if n else 0.0,
        "max_p0": max((x["p0_count"] for x in series), default=0),
        "dominance_max": max((x["dominance_ratio"] for x in series), default=0.0),
        "execution_triggered": any(x["execution_triggered"] for x in series),
        "runtime_mutation": any(x["runtime_mutation"] for x in series),
        "authority_leak_detected": any(x["authority_leak_detected"] for x in series),
    }
    status, hard, flags = _classify_stability(summary, series)
    summary["stability_status"] = status
    summary["hard_blockers"] = hard
    summary["review_flags"] = flags
    summary["patch_004_allowed"] = False
    return {"profile_id": profile_id, "summary": summary}


def run_profile_diagnostics(input_path: str, cycles: int = 30) -> Dict[str, Any]:
    base_payload = _load_json(Path(input_path))
    temp_dir = Path("tmp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    profiles = [_run_profile(base_payload, profile_id, cycles, temp_dir) for profile_id in PROFILE_IDS]
    by_id = {row["profile_id"]: row["summary"] for row in profiles}

    baseline = by_id["BASELINE_CURRENT"]
    no_flip = by_id["NO_FLIP"]
    low_drift = by_id["LOW_DRIFT"]
    high_drift = by_id["HIGH_DRIFT"]
    domain = by_id["DOMAIN_ROTATION"]

    if (
        no_flip["avg_brier"] <= baseline["avg_brier"] - 0.03
        and no_flip["avg_confidence"] >= baseline["avg_confidence"] + 0.05
    ):
        driver = "OUTCOME_FLIP"
        action = "Reduce or gate outcome flip perturbation during replay evidence collection."
    elif (
        low_drift["avg_brier"] <= baseline["avg_brier"] - 0.03
        and high_drift["avg_brier"] >= baseline["avg_brier"] + 0.03
    ):
        driver = "PROBABILITY_DRIFT"
        action = "Narrow probability drift envelope and recalibrate confidence under drift stress."
    elif abs(domain["avg_brier"] - baseline["avg_brier"]) >= 0.03:
        driver = "DOMAIN_VARIATION"
        action = "Audit domain assignment/ordering sensitivity and stabilize domain-conditioned replay surfaces."
    elif all(p["summary"]["avg_brier"] >= 0.15 for p in profiles):
        driver = "SIGNAL_WEAKNESS"
        action = "Increase signal quality/evidence depth before progression to execution gating."
    elif all(p["summary"]["avg_brier"] < 0.15 for p in profiles) and all(p["summary"]["avg_confidence"] < 0.25 for p in profiles):
        driver = "CONFIDENCE_PENALTY"
        action = "Tune confidence penalty calibration while preserving deterministic and fail-closed behavior."
    else:
        driver = "NOT_COMPUTABLE"
        action = "Collect additional profile evidence and inspect per-cycle deltas for unresolved variance source."

    safety_flags = {
        "execution_triggered": any(p["summary"]["execution_triggered"] for p in profiles),
        "runtime_mutation": any(p["summary"]["runtime_mutation"] for p in profiles),
        "authority_leak_detected": any(p["summary"]["authority_leak_detected"] for p in profiles),
    }

    return {
        "schema_version": "ABXReplayProfileDiagnostics.v1",
        "cycles_per_profile": cycles,
        "profiles": profiles,
        "diagnosis": {
            "dominant_failure_driver": driver,
            "recommended_next_action": action,
        },
        "safety_flags": safety_flags,
    }


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print(json.dumps({}, indent=2, sort_keys=True))
        return 1
    input_path = argv[1]
    cycles = 30
    if len(argv) > 2:
        if argv[2] == "--cycles" and len(argv) > 3:
            cycles = int(argv[3])
        else:
            cycles = int(argv[2])
    out = run_profile_diagnostics(input_path, cycles=cycles)
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
