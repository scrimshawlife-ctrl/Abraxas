from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping


def _clamp_probability(value: float) -> float:
    return min(max(value, 0.01), 0.99)


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _cycle_input(base_payload: Mapping[str, Any], cycle_index: int) -> Dict[str, Any]:
    payload = json.loads(json.dumps(base_payload))
    records = payload.get("records", []) if isinstance(payload.get("records", []), list) else []
    out_records: List[Dict[str, Any]] = []
    offset = (cycle_index % 5) * 0.02
    for idx, rec in enumerate(records):
        row = dict(rec) if isinstance(rec, dict) else {}
        raw_p = row.get("forecast_probability", row.get("probability"))
        try:
            p = float(raw_p)
            row["forecast_probability"] = _clamp_probability(p + offset)
        except (TypeError, ValueError):
            pass

        out_records.append(row)

    out_records = sorted(out_records, key=lambda r: str(r.get("domain", "")))
    payload["records"] = out_records
    payload["run_id"] = f"multi_cycle_{cycle_index:03d}"
    return payload


def _run_one_cycle(payload: Mapping[str, Any], cycle_index: int, temp_dir: Path) -> Dict[str, Any]:
    temp_path = temp_dir / f"replay_cycle_{cycle_index:03d}.json"
    temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    cmd = [sys.executable, "scripts/run_replay_cycle.py", temp_path.as_posix()]
    env = dict(**{"PYTHONPATH": "."})
    completed = subprocess.run(cmd, capture_output=True, text=True, check=False, env=env)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr or completed.stdout)
    return json.loads(completed.stdout)




def _classify_stability(metrics: Mapping[str, Any], cycle_series: List[Mapping[str, Any]]) -> tuple[str, list[str], list[str]]:
    hard_blockers: list[str] = []
    review_flags: list[str] = []
    cycle_count = int(metrics.get("cycle_count", 0) or 0)
    blocked_count = int(metrics.get("blocked_count", 0) or 0)
    avg_brier = metrics.get("avg_brier")
    avg_conf = metrics.get("avg_confidence")
    max_p0 = int(metrics.get("max_p0", 0) or 0)
    dominance_max = float(metrics.get("dominance_max", 0.0) or 0.0)

    if bool(metrics.get("execution_triggered", False)):
        hard_blockers.append("EXECUTION_TRIGGERED")
    if bool(metrics.get("runtime_mutation", False)):
        hard_blockers.append("RUNTIME_MUTATION")
    if bool(metrics.get("authority_leak_detected", False)):
        hard_blockers.append("AUTHORITY_LEAK")

    consecutive_p0 = 0
    max_consecutive_p0 = 0
    for cycle in cycle_series:
        if int(cycle.get("p0_count", 0) or 0) > 0:
            consecutive_p0 += 1
            max_consecutive_p0 = max(max_consecutive_p0, consecutive_p0)
        else:
            consecutive_p0 = 0
    if max_consecutive_p0 >= 3 and ((avg_conf is not None and float(avg_conf) >= 0.35) or dominance_max > 1.5):
        hard_blockers.append("PERSISTENT_P0")

    if hard_blockers:
        return "HARD_BLOCKED", hard_blockers, review_flags
    if cycle_count > 0 and blocked_count > cycle_count * 0.6 and max_p0 > 0:
        return "HARD_BLOCKED", ["HIGH_BLOCK_RATE_WITH_P0"], review_flags

    if (
        avg_conf is not None and float(avg_conf) < 0.35
        and avg_brier is not None and float(avg_brier) >= 0.15
        and dominance_max <= 1.5
    ):
        review_flags.append("LOW_CONFIDENCE")
        return "LOW_CONFIDENCE_REVIEW", hard_blockers, review_flags

    if (
        blocked_count > 0
        or int(metrics.get("review_required_count", 0) or 0) > 0
        or dominance_max > 1.5
        or max_p0 > 0
    ):
        review_flags.append("REQUIRES_REVIEW")
        return "REVIEW_REQUIRED", hard_blockers, review_flags

    if (
        avg_brier is not None and float(avg_brier) < 0.15
        and avg_conf is not None and float(avg_conf) >= 0.35
        and max_p0 == 0
        and dominance_max <= 1.5
    ):
        return "STABLE", hard_blockers, review_flags

    return "NOT_COMPUTABLE", hard_blockers, review_flags


def run_multi_cycle_replay(input_path: str, num_cycles: int = 10) -> Dict[str, Any]:
    base_payload = _load_json(Path(input_path))
    temp_dir = Path("tmp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    receipts: List[Dict[str, Any]] = []
    cycles: List[Dict[str, Any]] = []

    for i in range(num_cycles):
        cycle_payload = _cycle_input(base_payload, i)
        receipt = _run_one_cycle(cycle_payload, i, temp_dir)
        receipts.append(receipt)
        calibration = receipt.get("calibration", {}) if isinstance(receipt.get("calibration", {}), dict) else {}
        fusion = receipt.get("fusion", {}) if isinstance(receipt.get("fusion", {}), dict) else {}
        queue = receipt.get("operator_queue", {}) if isinstance(receipt.get("operator_queue", {}), dict) else {}
        cycles.append(
            {
                "cycle": i,
                "mean_brier": float(calibration.get("mean_brier", 0.0) or 0.0),
                "confidence": float(fusion.get("confidence", 0.0) or 0.0),
                "p0_count": int(queue.get("p0_count", 0) or 0),
                "dominance_ratio": float(fusion.get("dominance_ratio", 0.0) or 0.0),
                "cycle_status": str(receipt.get("cycle_status", "NOT_COMPUTABLE")),
                "execution_triggered": bool(receipt.get("execution_triggered", False)),
                "runtime_mutation": bool(receipt.get("runtime_mutation", False)),
                "authority_leak_detected": bool(receipt.get("authority_leak_detected", False)),
            }
        )

    cycle_count = len(cycles)
    pass_count = sum(1 for row in cycles if row["cycle_status"] == "PASS")
    review_required_count = sum(1 for row in cycles if row["cycle_status"] == "REVIEW_REQUIRED")
    blocked_count = sum(1 for row in cycles if row["cycle_status"] == "BLOCKED")
    avg_brier = sum(row["mean_brier"] for row in cycles) / cycle_count if cycle_count else 0.0
    avg_confidence = sum(row["confidence"] for row in cycles) / cycle_count if cycle_count else 0.0
    max_p0 = max((row["p0_count"] for row in cycles), default=0)
    dominance_max = max((row["dominance_ratio"] for row in cycles), default=0.0)

    summary = {
        "outcome_flip_enabled": False,
        "cycle_count": cycle_count,
        "pass_count": pass_count,
        "review_required_count": review_required_count,
        "blocked_count": blocked_count,
        "avg_brier": avg_brier,
        "avg_confidence": avg_confidence,
        "max_p0": max_p0,
        "dominance_max": dominance_max,
        "execution_triggered": any(row["execution_triggered"] for row in cycles),
        "runtime_mutation": any(row["runtime_mutation"] for row in cycles),
        "authority_leak_detected": any(row["authority_leak_detected"] for row in cycles),
    }
    status, hard_blockers, review_flags = _classify_stability(summary, cycles)
    summary["stability_status"] = status
    summary["hard_blockers"] = hard_blockers
    summary["review_flags"] = review_flags

    cycle_count_required = 30
    evidence_window_status = "SUFFICIENT" if cycle_count >= cycle_count_required else "INSUFFICIENT"

    design_pass_allowed = (
        cycle_count >= cycle_count_required
        and blocked_count == 0
        and max_p0 == 0
        and hard_blockers == []
        and summary["execution_triggered"] is False
        and summary["runtime_mutation"] is False
        and summary["authority_leak_detected"] is False
        and avg_brier <= 0.15
        and dominance_max <= 1.5
    )

    if design_pass_allowed:
        readiness_status = "READY_FOR_DESIGN"
        summary["stability_status"] = "PASS_WITH_REVIEW"
        patch_004_allowed = True
    else:
        readiness_status = "READY" if status == "STABLE" else status
        patch_004_allowed = evidence_window_status == "SUFFICIENT" and readiness_status == "READY"

    summary["cycle_count_observed"] = cycle_count
    summary["cycle_count_required"] = cycle_count_required
    summary["evidence_window_status"] = evidence_window_status
    summary["readiness_status"] = readiness_status
    summary["design_pass_allowed"] = design_pass_allowed
    summary["execution_allowed"] = False
    summary["low_confidence_review"] = avg_confidence < 0.25
    summary["readiness_reason"] = "design_pass_threshold_met" if design_pass_allowed else "design_pass_threshold_not_met"
    summary["patch_004_allowed"] = patch_004_allowed

    out_dir = Path("out") / "replay"
    if out_dir.exists():
        ledger_path = out_dir / "multi_cycle.jsonl"
        with ledger_path.open("a", encoding="utf-8") as fh:
            for receipt in receipts:
                fh.write(json.dumps({"type": "receipt", "value": receipt}, sort_keys=True) + "\n")
            fh.write(json.dumps({"type": "summary", "value": summary}, sort_keys=True) + "\n")

    return {"summary": summary, "cycles": cycles}


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print(json.dumps({"summary": {}, "cycles": []}, indent=2, sort_keys=True))
        return 1
    input_path = argv[1]
    num_cycles = 10
    if len(argv) > 2:
        if argv[2] == "--cycles" and len(argv) > 3:
            num_cycles = int(argv[3])
        else:
            num_cycles = int(argv[2])
    output = run_multi_cycle_replay(input_path, num_cycles=num_cycles)
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
