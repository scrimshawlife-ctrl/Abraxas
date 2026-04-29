from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping

from scripts.run_replay_cycle import run_replay_cycle


def _clamp_probability(value: float) -> float:
    return min(max(value, 0.01), 0.99)


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _cycle_input(base_payload: Mapping[str, Any], cycle_index: int) -> Dict[str, Any]:
    payload = json.loads(json.dumps(base_payload))
    records = payload.get("records", []) if isinstance(payload.get("records", []), list) else []
    out: List[Dict[str, Any]] = []
    offset = (cycle_index % 5) * 0.02
    for rec in records:
        row = dict(rec) if isinstance(rec, dict) else {}
        raw_p = row.get("forecast_probability", row.get("probability"))
        try:
            row["forecast_probability"] = _clamp_probability(float(raw_p) + offset)
        except (TypeError, ValueError):
            pass
        out.append(row)
    out = sorted(out, key=lambda r: str(r.get("domain", "")))
    payload["records"] = out
    payload["run_id"] = f"review_diag_{cycle_index:03d}"
    return payload


def _recommended_action(driver: str) -> str:
    mapping = {
        "PROOF_HASH_BLOCK": "fix proof hashing / artifact linking",
        "P1_REVIEW_ITEM_PERSISTENCE": "inspect repeated P1 causes",
        "CONFIDENCE_THRESHOLD": "adjust confidence thresholds or window",
        "PASS_LOGIC_TOO_STRICT": "relax pass classifier",
        "DOMINANCE_DRIFT": "inspect fusion behavior",
        "NOT_COMPUTABLE": "missing data",
    }
    return mapping.get(driver, "missing data")


def run_review_saturation_diagnostic(input_path: str, cycles: int = 30) -> Dict[str, Any]:
    base = _load_json(Path(input_path))
    temp_dir = Path("tmp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    cycle_rows: List[Dict[str, Any]] = []
    for i in range(cycles):
        payload = _cycle_input(base, i)
        p = temp_dir / f"review_diag_{i:03d}.json"
        p.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        receipt = run_replay_cycle(p.as_posix())
        cal = receipt.get("calibration", {}) if isinstance(receipt.get("calibration", {}), dict) else {}
        fus = receipt.get("fusion", {}) if isinstance(receipt.get("fusion", {}), dict) else {}
        q = receipt.get("operator_queue", {}) if isinstance(receipt.get("operator_queue", {}), dict) else {}
        proof = receipt.get("proof_state_set", {}) if isinstance(receipt.get("proof_state_set", {}), dict) else {}

        confidence = float(fus.get("confidence", 0.0) or 0.0)
        dominance_ratio = float(fus.get("dominance_ratio", 0.0) or 0.0)
        p1_count = int(q.get("p1_count", 0) or 0)
        disp_allowed = int(proof.get("display_allowed_count", 0) or 0)
        not_comp_proof = int(proof.get("not_computable_count", 0) or 0)

        row = {
            "cycle_status": str(receipt.get("cycle_status", "NOT_COMPUTABLE")),
            "mean_brier": float(cal.get("mean_brier", 0.0) or 0.0),
            "confidence": confidence,
            "p0_count": int(q.get("p0_count", 0) or 0),
            "dominance_ratio": dominance_ratio,
            "low_confidence": confidence < 0.35,
            "dominance_drift": dominance_ratio > 1.5,
            "p1_review_items": p1_count > 0,
            "proof_hash_block": disp_allowed == 0 and not_comp_proof > 0,
            "not_computable_proof": not_comp_proof > 0,
            "execution_triggered": bool(receipt.get("execution_triggered", False)),
            "runtime_mutation": bool(receipt.get("runtime_mutation", False)),
            "authority_leak_detected": bool(receipt.get("authority_leak_detected", False)),
        }

        has_primary = row["low_confidence"] or row["dominance_drift"] or row["p1_review_items"] or row["proof_hash_block"] or row["not_computable_proof"]
        row["other"] = row["cycle_status"] == "REVIEW_REQUIRED" and not has_primary
        cycle_rows.append(row)

    n = len(cycle_rows)
    pass_count = sum(1 for r in cycle_rows if r["cycle_status"] == "PASS")
    review_required_count = sum(1 for r in cycle_rows if r["cycle_status"] == "REVIEW_REQUIRED")
    blocked_count = sum(1 for r in cycle_rows if r["cycle_status"] == "BLOCKED")
    avg_brier = sum(r["mean_brier"] for r in cycle_rows) / n if n else 0.0
    avg_confidence = sum(r["confidence"] for r in cycle_rows) / n if n else 0.0
    max_p0 = max((r["p0_count"] for r in cycle_rows), default=0)
    dominance_max = max((r["dominance_ratio"] for r in cycle_rows), default=0.0)

    cause_counts = {
        "low_confidence": sum(1 for r in cycle_rows if r["low_confidence"]),
        "dominance_drift": sum(1 for r in cycle_rows if r["dominance_drift"]),
        "p1_review_items": sum(1 for r in cycle_rows if r["p1_review_items"]),
        "proof_hash_block": sum(1 for r in cycle_rows if r["proof_hash_block"]),
        "not_computable_proof": sum(1 for r in cycle_rows if r["not_computable_proof"]),
        "other": sum(1 for r in cycle_rows if r["other"]),
    }

    if n and cause_counts["proof_hash_block"] >= n * 0.7:
        driver = "PROOF_HASH_BLOCK"
    elif n and cause_counts["p1_review_items"] >= n * 0.7:
        driver = "P1_REVIEW_ITEM_PERSISTENCE"
    elif n and cause_counts["low_confidence"] >= n * 0.7:
        driver = "CONFIDENCE_THRESHOLD"
    elif n and cause_counts["dominance_drift"] >= n * 0.3:
        driver = "DOMINANCE_DRIFT"
    elif pass_count == 0 and blocked_count == 0 and max_p0 == 0 and avg_brier < 0.1:
        driver = "PASS_LOGIC_TOO_STRICT"
    else:
        driver = "NOT_COMPUTABLE"

    safety_flags = {
        "execution_triggered": any(r["execution_triggered"] for r in cycle_rows),
        "runtime_mutation": any(r["runtime_mutation"] for r in cycle_rows),
        "authority_leak_detected": any(r["authority_leak_detected"] for r in cycle_rows),
    }

    return {
        "schema_version": "ABXReviewSaturationDiagnostic.v1",
        "cycle_count": cycles,
        "summary": {
            "pass_count": pass_count,
            "review_required_count": review_required_count,
            "blocked_count": blocked_count,
            "avg_brier": avg_brier,
            "avg_confidence": avg_confidence,
            "max_p0": max_p0,
            "dominance_max": dominance_max,
        },
        "cycle_cause_counts": cause_counts,
        "dominant_review_driver": driver,
        "recommended_next_action": _recommended_action(driver),
        "patch_004_allowed": False,
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
    output = run_review_saturation_diagnostic(input_path, cycles=cycles)
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
