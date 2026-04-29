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
    payload["run_id"] = f"p0_diag_{cycle_index:03d}"
    return payload


def _recommended_action(cause: str) -> str:
    mapping = {
        "CALIBRATION_FAIL": "inspect Brier + prediction quality",
        "CALIBRATION_NOT_COMPUTABLE": "fix missing inputs",
        "PROMOTION_GATE_BLOCKED": "inspect gate logic",
        "SAMPLE_SIZE_UNDER_MIN": "increase resolved outcomes",
        "INPUT_NOT_COMPUTABLE_SPIKE": "fix dataset",
        "OPERATOR_QUEUE_POLICY": "refine P0 rules",
        "PROOF_P0_LINK": "inspect linkage",
        "REPLAY_VARIATION_EDGE": "inspect perturbation logic",
        "NOT_COMPUTABLE": "missing data",
    }
    return mapping.get(cause, "missing data")


def run_p0_root_cause_diagnostic(input_path: str, cycles: int = 30) -> Dict[str, Any]:
    base = _load_json(Path(input_path))
    temp_dir = Path("tmp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    counts = {
        "calibration_not_computable": 0,
        "calibration_fail": 0,
        "promotion_gate_blocked": 0,
        "sample_size_under_min": 0,
        "input_not_computable_spike": 0,
        "proof_p0_link": 0,
        "operator_queue_policy": 0,
        "replay_variation_edge": 0,
        "not_computable": 0,
    }
    p0_cycle_indices: list[int] = []
    p0_examples: list[dict[str, Any]] = []
    cycle_offsets: list[int] = []
    safety = {"execution_triggered": False, "runtime_mutation": False, "authority_leak_detected": False}

    for i in range(cycles):
        payload = _cycle_input(base, i)
        p = temp_dir / f"p0_diag_{i:03d}.json"
        p.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        receipt = run_replay_cycle(p.as_posix(), write_artifacts=True)

        q = receipt.get("operator_queue", {}) if isinstance(receipt.get("operator_queue", {}), dict) else {}
        p0_count = int(q.get("p0_count", 0) or 0)
        if p0_count <= 0:
            continue

        p0_cycle_indices.append(i)
        cycle_offsets.append(i % 5)

        cal = receipt.get("calibration", {}) if isinstance(receipt.get("calibration", {}), dict) else {}
        proof = receipt.get("proof_state_set", {}) if isinstance(receipt.get("proof_state_set", {}), dict) else {}
        items = q.get("items", []) if isinstance(q.get("items", []), list) else []

        cal_status = str(cal.get("calibration_drift_status", "NOT_COMPUTABLE"))
        gate = str(cal.get("promotion_gate_status", "NOT_COMPUTABLE"))
        sample_size = int(cal.get("sample_size", 0) or 0)
        not_comp = int(receipt.get("not_computable_count", 0) or 0)
        resolved = int(receipt.get("resolved_count", 0) or 0)
        total = int(receipt.get("input_record_count", 0) or 0)

        p0_review_ids = {
            str(item.get("review_id", ""))
            for item in items
            if isinstance(item, dict) and str(item.get("priority", "")) == "P0"
        }
        proof_items = proof.get("items", []) if isinstance(proof.get("items", []), list) else []
        proof_p0_link = any(
            isinstance(row, dict) and str(row.get("operator_review_item_id", "")) in p0_review_ids
            for row in proof_items
        )

        if cal_status == "NOT_COMPUTABLE":
            counts["calibration_not_computable"] += 1
        if cal_status == "FAIL":
            counts["calibration_fail"] += 1
        if gate in {"BLOCKED", "FAIL"}:
            counts["promotion_gate_blocked"] += 1
        if sample_size < 3:
            counts["sample_size_under_min"] += 1
        if total > 0 and (not_comp > resolved or not_comp > 0.3 * total):
            counts["input_not_computable_spike"] += 1
        if proof_p0_link:
            counts["proof_p0_link"] += 1
        if p0_count > 0 and cal_status in {"PASS", "REVIEW_REQUIRED"} and gate == "PASS":
            counts["operator_queue_policy"] += 1

        if len(cycle_offsets) > 1 and len(set(cycle_offsets)) < len(cycle_offsets):
            counts["replay_variation_edge"] += 1

        if not any([cal_status, gate]) or total == 0:
            counts["not_computable"] += 1

        if len(p0_examples) < 5:
            p0_examples.append(
                {
                    "cycle_index": i,
                    "p0_count": p0_count,
                    "calibration_drift_status": cal_status,
                    "promotion_gate_status": gate,
                    "sample_size": sample_size,
                    "not_computable_count": not_comp,
                    "resolved_count": resolved,
                    "input_record_count": total,
                }
            )

        safety["execution_triggered"] = safety["execution_triggered"] or bool(receipt.get("execution_triggered", False))
        safety["runtime_mutation"] = safety["runtime_mutation"] or bool(receipt.get("runtime_mutation", False))
        safety["authority_leak_detected"] = safety["authority_leak_detected"] or bool(receipt.get("authority_leak_detected", False))

    precedence = [
        ("CALIBRATION_FAIL", "calibration_fail"),
        ("CALIBRATION_NOT_COMPUTABLE", "calibration_not_computable"),
        ("PROMOTION_GATE_BLOCKED", "promotion_gate_blocked"),
        ("SAMPLE_SIZE_UNDER_MIN", "sample_size_under_min"),
        ("INPUT_NOT_COMPUTABLE_SPIKE", "input_not_computable_spike"),
        ("OPERATOR_QUEUE_POLICY", "operator_queue_policy"),
        ("PROOF_P0_LINK", "proof_p0_link"),
        ("REPLAY_VARIATION_EDGE", "replay_variation_edge"),
        ("NOT_COMPUTABLE", "not_computable"),
    ]
    dominant = "NOT_COMPUTABLE"
    best = 0
    for label, key in precedence:
        if counts[key] > best:
            best = counts[key]
            dominant = label

    return {
        "schema_version": "ABXP0RootCauseDiagnostic.v1",
        "cycle_count": cycles,
        "p0_cycle_count": len(p0_cycle_indices),
        "p0_cycle_indices": p0_cycle_indices,
        "p0_cause_counts": counts,
        "dominant_p0_cause": dominant,
        "p0_examples": p0_examples,
        "recommended_next_action": _recommended_action(dominant),
        "patch_004_allowed": False,
        "safety_flags": safety,
    }


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print(json.dumps({}, indent=2, sort_keys=True))
        return 1
    input_path = argv[1]
    cycles = 30
    if len(argv) > 2:
        flag = argv[2].replace("–", "-")
        if flag in {"--cycles", "-cycles"} and len(argv) > 3:
            cycles = int(argv[3])
        else:
            cycles = int(flag)
    out = run_p0_root_cause_diagnostic(input_path, cycles=cycles)
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
