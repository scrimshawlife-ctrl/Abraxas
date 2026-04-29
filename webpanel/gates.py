from __future__ import annotations

from typing import Any, Dict, List, Optional

from abx.calibration.report_builder import build_calibration_report
from abx.calibration.ledger_writer import write_calibration_report
from abx.weighting.advisory_builder import build_domain_weight_advisory
from abx.weighting.ledger_writer import write_domain_weight_advisory
from abx.fusion.fusion_builder import build_fusion_projection
from abx.fusion.ledger_writer import write_fusion_projection
from abx.operator.ledger_writer import write_operator_queue
from abx.operator.queue_builder import build_operator_queue
from abx.operator.review_builder import build_review_items
from abx.viz.ledger_writer import write_aal_viz_proof_state_set
from abx.viz.proof_builder import build_proof_states
from abx.viz.set_builder import build_proof_state_set
from webpanel.oracle_output import extract_oracle_output
from webpanel.policy_gate import policy_ack_required


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _drift_class_from_oracle(oracle: Dict[str, Any]) -> Optional[str]:
    provenance = _safe_dict(oracle.get("provenance"))
    stability = _safe_dict(provenance.get("stability_status"))
    drift = stability.get("drift_class")
    if isinstance(drift, str) and drift.strip():
        return drift.strip()
    return None


def _drift_class_from_stability(run: Any) -> Optional[str]:
    report = getattr(run, "stability_report", None)
    if not isinstance(report, dict):
        return None
    drift = report.get("drift_class")
    if isinstance(drift, str) and drift.strip():
        return drift.strip()
    return None


def _effective_drift_class(run: Any) -> str:
    oracle = extract_oracle_output(run)
    if oracle:
        drift = _drift_class_from_oracle(oracle)
        if drift:
            return drift
    drift = _drift_class_from_stability(run)
    return drift or "unknown"


def compute_gate_stack(run: Any, current_policy_hash: Optional[str]) -> List[Dict[str, Any]]:
    gates: List[Dict[str, Any]] = []

    if policy_ack_required(run, current_policy_hash):
        gates.append(
            {
                "code": "policy_ack_required",
                "severity": "block",
                "message": "Policy changed since ingest.",
                "remedy": "ACK policy change.",
                "priority": 1,
            }
        )

    max_steps = int(getattr(run, "session_max_steps", 0) or 0)
    used_steps = int(getattr(run, "session_steps_used", 0) or 0)
    if max_steps > 0 and used_steps >= max_steps:
        gates.append(
            {
                "code": "session_exhausted",
                "severity": "block",
                "message": "Session budget exhausted.",
                "remedy": "Start a new session.",
                "priority": 2,
            }
        )
    if not bool(getattr(run, "session_active", False)):
        gates.append(
            {
                "code": "session_inactive",
                "severity": "block",
                "message": "Session inactive.",
                "remedy": "Start a session.",
                "priority": 3,
            }
        )

    drift_class = _effective_drift_class(run)
    if drift_class not in {"none", "unknown"}:
        gates.append(
            {
                "code": "drift_blocked",
                "severity": "block",
                "message": f"Drift class: {drift_class}.",
                "remedy": "Re-run stabilization.",
                "priority": 4,
            }
        )

    signal = getattr(run, "signal", None)
    provenance_status = getattr(signal, "provenance_status", None)
    if provenance_status in {"missing", "partial"}:
        gates.append(
            {
                "code": "provenance_missing",
                "severity": "warn",
                "message": f"Provenance status: {provenance_status}.",
                "remedy": "Provide provenance artifacts.",
                "priority": 5,
            }
        )

    invariance_status = getattr(signal, "invariance_status", None)
    if invariance_status == "fail":
        gates.append(
            {
                "code": "invariance_failed",
                "severity": "warn",
                "message": "Invariance check failed.",
                "remedy": "Provide invariance artifacts.",
                "priority": 5,
            }
        )

    actions_remaining = getattr(run, "actions_remaining", None)
    if actions_remaining is not None and actions_remaining <= 0:
        gates.append(
            {
                "code": "quota_exhausted",
                "severity": "block",
                "message": "Deferral quota exhausted.",
                "remedy": "Start a new deferral session.",
                "priority": 6,
            }
        )

    gates = sorted(gates, key=lambda g: (g.get("priority", 99), g.get("code", "")))
    return gates


def build_calibration_drift_report(
    run: Any,
    current_policy_hash: Optional[str],
    *,
    write_ledger: bool = False,
    include_weight_advisory: bool = True,
    write_advisory_ledger: bool = False,
    include_fusion_projection: bool = True,
    write_fusion_ledger: bool = False,
    include_operator_queue: bool = True,
    write_operator_queue_ledger: bool = False,
    include_viz_proof_state: bool = True,
    write_viz_proof_ledger: bool = False,
) -> Dict[str, Any]:
    gates = compute_gate_stack(run, current_policy_hash)
    drift_class = _effective_drift_class(run)
    signal = getattr(run, "signal", None)
    provenance_status = getattr(signal, "provenance_status", None)
    has_missing_inputs = provenance_status in {"missing", "partial"}

    block_codes = [str(g.get("code", "")) for g in gates if str(g.get("severity", "")) == "block"]
    if not gates:
        promotion_status = "PASS"
    elif block_codes:
        promotion_status = "BLOCKED"
    else:
        promotion_status = "NOT_COMPUTABLE"

    dominant_failure_mode = block_codes[0] if block_codes else ("none" if promotion_status == "PASS" else "review_required")

    report = build_calibration_report(
        drift_metrics={
            "drift_class": drift_class,
            "mean_brier": 0.0,
            "sample_size": 0,
            "not_computable_count": 1 if has_missing_inputs else 0,
            "has_missing_inputs": has_missing_inputs,
        },
        gate_state={
            "promotion_gate_status": promotion_status,
            "dominant_failure_mode": dominant_failure_mode,
        },
        evidence_refs=[
            "webpanel.gates.compute_gate_stack",
            "webpanel.gates._effective_drift_class",
            "webpanel.osl_v2.build_oracle_output_v2",
        ],
    )

    ledger_path = write_calibration_report(report) if write_ledger else None
    result: Dict[str, Any] = {"report": report}
    if ledger_path:
        result["ledger_path"] = ledger_path

    if include_weight_advisory:
        advisory = build_domain_weight_advisory(report)
        result["domain_weight_advisory"] = advisory
        advisory_ledger_path = write_domain_weight_advisory(advisory) if write_advisory_ledger else None
        if advisory_ledger_path:
            result["domain_weight_advisory_ledger_path"] = advisory_ledger_path

        if include_fusion_projection:
            fusion_projection = build_fusion_projection(report, advisory)
            result["fusion_projection"] = fusion_projection
            fusion_ledger_path = write_fusion_projection(fusion_projection) if write_fusion_ledger else None
            if fusion_ledger_path:
                result["fusion_projection_ledger_path"] = fusion_ledger_path

            if include_operator_queue:
                review_items = build_review_items(report, advisory, fusion_projection)
                operator_queue = build_operator_queue(review_items)
                result["operator_review_items"] = review_items
                result["operator_queue"] = operator_queue
                operator_queue_ledger_path = write_operator_queue(operator_queue) if write_operator_queue_ledger else None
                if operator_queue_ledger_path:
                    result["operator_queue_ledger_path"] = operator_queue_ledger_path

                if include_viz_proof_state:
                    proof_states = build_proof_states(report, advisory, fusion_projection, operator_queue)
                    proof_state_set = build_proof_state_set(proof_states)
                    result["proof_states"] = proof_states
                    result["proof_state_set"] = proof_state_set
                    viz_ledger_path = write_aal_viz_proof_state_set(proof_state_set) if write_viz_proof_ledger else None
                    if viz_ledger_path:
                        result["proof_state_set_ledger_path"] = viz_ledger_path
    return result
