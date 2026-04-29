from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping

from abx.calibration.report_builder import build_calibration_report
from abx.fusion.fusion_builder import build_fusion_projection
from abx.operator.queue_builder import build_operator_queue
from abx.operator.review_builder import build_review_items
from abx.viz.proof_builder import build_proof_states
from abx.viz.set_builder import build_proof_state_set
from abx.weighting.advisory_builder import build_domain_weight_advisory


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_id() -> str:
    return f"replay-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


def _not_computable_receipt(*, run_id: str, input_count: int = 0, pending_count: int = 0, not_computable_count: int = 0) -> Dict[str, Any]:
    return {
        "schema_version": "ABXReplayRunReceipt.v1",
        "run_id": run_id,
        "created_at": _utc_now(),
        "input_record_count": input_count,
        "resolved_count": 0,
        "pending_count": pending_count,
        "not_computable_count": not_computable_count,
        "calibration": {},
        "advisory": {},
        "fusion": {},
        "operator_queue": {},
        "proof_state_set": {},
        "execution_triggered": False,
        "runtime_mutation": False,
        "authority_leak_detected": False,
        "cycle_status": "NOT_COMPUTABLE",
    }


def _parse_records(payload: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    records = payload.get("records", [])
    if not isinstance(records, list):
        return []
    return [r for r in records if isinstance(r, Mapping)]


def run_replay_cycle(input_path: str) -> Dict[str, Any]:
    run_id = _run_id()
    path = Path(input_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return _not_computable_receipt(run_id=run_id)

    if not isinstance(payload, Mapping):
        return _not_computable_receipt(run_id=run_id)
    if str(payload.get("schema_version", "")) != "ABXReplayInput.v1":
        return _not_computable_receipt(run_id=run_id)

    records = _parse_records(payload)
    if not records:
        return _not_computable_receipt(run_id=run_id)

    resolved: list[tuple[float, int]] = []
    pending_count = 0
    not_computable_count = 0
    for rec in records:
        outcome = str(rec.get("outcome", "")).upper()
        p_raw = rec.get("forecast_probability", rec.get("probability"))
        try:
            p = float(p_raw)
        except (TypeError, ValueError):
            p = None

        if outcome == "PENDING":
            pending_count += 1
            continue
        if outcome in {"YES", "NO"} and p is not None:
            o = 1 if outcome == "YES" else 0
            resolved.append((p, o))
        else:
            not_computable_count += 1

    if not resolved:
        return _not_computable_receipt(
            run_id=run_id,
            input_count=len(records),
            pending_count=pending_count,
            not_computable_count=not_computable_count,
        )

    brier_scores = [(p - o) ** 2 for p, o in resolved]
    mean_brier = sum(brier_scores) / float(len(brier_scores))
    sample_size = len(resolved)
    promotion_gate_status = "BLOCKED" if sample_size < 3 else "PASS"

    report = build_calibration_report(
        drift_metrics={
            "drift_class": "none" if promotion_gate_status == "PASS" else "major",
            "mean_brier": mean_brier,
            "sample_size": sample_size,
            "not_computable_count": not_computable_count,
            "has_missing_inputs": False,
        },
        gate_state={
            "promotion_gate_status": promotion_gate_status,
            "dominant_failure_mode": "insufficient_sample_size" if sample_size < 3 else "none",
        },
        evidence_refs=["scripts.run_replay_cycle", "abx.calibration.report_builder.build_calibration_report"],
    )

    advisory = build_domain_weight_advisory(report)
    fusion = build_fusion_projection(report, advisory)
    review_items = build_review_items(report, advisory, fusion)
    queue = build_operator_queue(review_items)
    proof_states = build_proof_states(report, advisory, fusion, queue)
    proof_set = build_proof_state_set(proof_states)

    p0_count = int(queue.get("p0_count", 0) or 0)
    p1_count = int(queue.get("p1_count", 0) or 0)
    if not resolved:
        cycle_status = "NOT_COMPUTABLE"
    elif promotion_gate_status != "PASS" or p0_count > 0:
        cycle_status = "BLOCKED"
    elif p1_count > 0:
        cycle_status = "REVIEW_REQUIRED"
    else:
        cycle_status = "PASS"

    receipt = {
        "schema_version": "ABXReplayRunReceipt.v1",
        "run_id": run_id,
        "created_at": _utc_now(),
        "input_record_count": len(records),
        "resolved_count": len(resolved),
        "pending_count": pending_count,
        "not_computable_count": not_computable_count,
        "calibration": report,
        "advisory": advisory,
        "fusion": fusion,
        "operator_queue": queue,
        "proof_state_set": proof_set,
        "execution_triggered": False,
        "runtime_mutation": False,
        "authority_leak_detected": False,
        "cycle_status": cycle_status,
    }

    out_dir = Path("out") / "replay"
    if out_dir.exists():
        path_out = out_dir / "replay_runs.jsonl"
        with path_out.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(receipt, sort_keys=True) + "\n")

    return receipt


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print(json.dumps(_not_computable_receipt(run_id=_run_id()), indent=2, sort_keys=True))
        return 1
    receipt = run_replay_cycle(argv[1])
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
