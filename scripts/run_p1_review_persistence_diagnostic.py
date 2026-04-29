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
    payload["run_id"] = f"p1_diag_{cycle_index:03d}"
    return payload


def _recommended_action(driver: str) -> str:
    mapping = {
        "PROOF_VISIBILITY_PARTIAL": "fix proof gating / linking",
        "LOW_CONFIDENCE_THRESHOLD": "adjust thresholds (NOT math)",
        "OPERATOR_QUEUE_P1_POLICY": "refine P1 generation",
        "REVIEW_FLAG_POLICY": "refine stability classifier",
        "READINESS_GATE_POLICY": "relax PASS gating logic",
        "NOT_COMPUTABLE": "missing data",
    }
    return mapping.get(driver, "missing data")


def run_p1_review_persistence_diagnostic(input_path: str, cycles: int = 30) -> Dict[str, Any]:
    base = _load_json(Path(input_path))
    temp_dir = Path("tmp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    cycle_rows: List[Dict[str, Any]] = []
    for i in range(cycles):
        payload = _cycle_input(base, i)
        p = temp_dir / f"p1_diag_{i:03d}.json"
        p.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        receipt = run_replay_cycle(p.as_posix(), write_artifacts=True)

        cal = receipt.get("calibration", {}) if isinstance(receipt.get("calibration", {}), dict) else {}
        fus = receipt.get("fusion", {}) if isinstance(receipt.get("fusion", {}), dict) else {}
        queue = receipt.get("operator_queue", {}) if isinstance(receipt.get("operator_queue", {}), dict) else {}
        proof = receipt.get("proof_state_set", {}) if isinstance(receipt.get("proof_state_set", {}), dict) else {}

        drift_alerts = fus.get("drift_alerts", []) if isinstance(fus.get("drift_alerts", []), list) else []
        confidence = float(fus.get("confidence", 0.0) or 0.0)
        dominance_ratio = float(fus.get("dominance_ratio", 0.0) or 0.0)
        p0_count = int(queue.get("p0_count", 0) or 0)
        p1_count = int(queue.get("p1_count", 0) or 0)
        display_allowed_count = int(proof.get("display_allowed_count", 0) or 0)
        total_items = int(proof.get("total_items", 0) or 0)
        cycle_status = str(receipt.get("cycle_status", "NOT_COMPUTABLE"))

        low_confidence_fusion = confidence < 0.35 or "LOW_CONFIDENCE" in drift_alerts
        dominance_imbalance = dominance_ratio > 1.5 or "DOMAIN_DOMINANCE_DRIFT" in drift_alerts
        proof_visibility_block = display_allowed_count < total_items
        operator_policy_review = p1_count > 0
        classifier_review_flag = cycle_status == "REVIEW_REQUIRED" and p0_count == 0 and cycle_status != "BLOCKED"

        row = {
            "cycle_status": cycle_status,
            "mean_brier": float(cal.get("mean_brier", 0.0) or 0.0),
            "confidence": confidence,
            "p0_count": p0_count,
            "p1_count": p1_count,
            "dominance_ratio": dominance_ratio,
            "low_confidence_fusion": low_confidence_fusion,
            "dominance_imbalance": dominance_imbalance,
            "proof_visibility_block": proof_visibility_block,
            "operator_policy_review": operator_policy_review,
            "classifier_review_flag": classifier_review_flag,
            "execution_triggered": bool(receipt.get("execution_triggered", False)),
            "runtime_mutation": bool(receipt.get("runtime_mutation", False)),
            "authority_leak_detected": bool(receipt.get("authority_leak_detected", False)),
        }
        has_primary = (
            low_confidence_fusion
            or dominance_imbalance
            or proof_visibility_block
            or operator_policy_review
            or classifier_review_flag
        )
        row["other"] = cycle_status == "REVIEW_REQUIRED" and not has_primary
        cycle_rows.append(row)

    n = len(cycle_rows)
    pass_count = sum(1 for r in cycle_rows if r["cycle_status"] == "PASS")
    review_required_count = sum(1 for r in cycle_rows if r["cycle_status"] == "REVIEW_REQUIRED")
    blocked_count = sum(1 for r in cycle_rows if r["cycle_status"] == "BLOCKED")
    avg_brier = sum(r["mean_brier"] for r in cycle_rows) / n if n else 0.0
    avg_confidence = sum(r["confidence"] for r in cycle_rows) / n if n else 0.0
    max_p0 = max((r["p0_count"] for r in cycle_rows), default=0)
    max_p1 = max((r["p1_count"] for r in cycle_rows), default=0)
    dominance_max = max((r["dominance_ratio"] for r in cycle_rows), default=0.0)

    reason_counts = {
        "low_confidence_fusion": sum(1 for r in cycle_rows if r["low_confidence_fusion"]),
        "dominance_imbalance": sum(1 for r in cycle_rows if r["dominance_imbalance"]),
        "proof_visibility_block": sum(1 for r in cycle_rows if r["proof_visibility_block"]),
        "operator_policy_review": sum(1 for r in cycle_rows if r["operator_policy_review"]),
        "classifier_review_flag": sum(1 for r in cycle_rows if r["classifier_review_flag"]),
        "other": sum(1 for r in cycle_rows if r["other"]),
    }

    if n and reason_counts["proof_visibility_block"] >= n * 0.7:
        driver = "PROOF_VISIBILITY_PARTIAL"
    elif n and reason_counts["low_confidence_fusion"] >= n * 0.7:
        driver = "LOW_CONFIDENCE_THRESHOLD"
    elif n and reason_counts["operator_policy_review"] >= n * 0.7:
        driver = "OPERATOR_QUEUE_P1_POLICY"
    elif n and reason_counts["classifier_review_flag"] >= n * 0.7:
        driver = "REVIEW_FLAG_POLICY"
    elif pass_count == 0 and blocked_count == 0 and max_p0 == 0:
        driver = "READINESS_GATE_POLICY"
    else:
        driver = "NOT_COMPUTABLE"

    safety_flags = {
        "execution_triggered": any(r["execution_triggered"] for r in cycle_rows),
        "runtime_mutation": any(r["runtime_mutation"] for r in cycle_rows),
        "authority_leak_detected": any(r["authority_leak_detected"] for r in cycle_rows),
    }

    return {
        "schema_version": "ABXP1ReviewPersistenceDiagnostic.v1",
        "cycle_count": cycles,
        "summary": {
            "avg_brier": avg_brier,
            "avg_confidence": avg_confidence,
            "pass_count": pass_count,
            "review_required_count": review_required_count,
            "blocked_count": blocked_count,
            "max_p0": max_p0,
            "max_p1": max_p1,
            "dominance_max": dominance_max,
        },
        "p1_reason_counts": reason_counts,
        "dominant_p1_driver": driver,
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
        cycle_flag = argv[2].replace("–", "-")
        if cycle_flag in {"--cycles", "-cycles"} and len(argv) > 3:
            cycles = int(argv[3])
        else:
            cycles = int(cycle_flag)
    out = run_p1_review_persistence_diagnostic(input_path, cycles=cycles)
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
