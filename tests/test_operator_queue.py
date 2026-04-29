from abx.operator.queue_builder import build_operator_queue
from abx.operator.review_builder import build_review_items
from abx.weighting.advisory_builder import build_domain_weight_advisory
from abx.fusion.fusion_builder import build_fusion_projection
from webpanel.gates import build_calibration_drift_report


def _report(status: str) -> dict:
    return {
        "schema_version": "CalibrationDriftReport.v1",
        "generated_at": "2026-01-01T00:00:00+00:00",
        "mean_brier": 0.0,
        "sample_size": 0,
        "not_computable_count": 0,
        "calibration_drift_status": status,
        "promotion_gate_status": "PASS",
        "dominant_failure_mode": "none",
        "evidence_refs": ["report.ref"],
    }


def test_operator_queue_schema_and_counts():
    report = _report("FAIL")
    advisory = build_domain_weight_advisory(report)
    fusion = build_fusion_projection(report, advisory)
    items = build_review_items(report, advisory, fusion)
    queue = build_operator_queue(items)

    assert queue["schema_version"] == "OperatorQueue.v1"
    assert queue["total_items"] == len(queue["items"])
    assert queue["p0_count"] + queue["p1_count"] + queue["p2_count"] == queue["total_items"]


def test_deterministic_ordering_priority_source_review_id():
    items = [
        {
            "schema_version": "OperatorReviewItem.v1",
            "review_id": "b",
            "created_at": "2026-01-01T00:00:00+00:00",
            "source_system": "fusion",
            "decision_type": "REVIEW",
            "priority": "P1",
            "reason": "r",
            "evidence_refs": [],
            "operator_required": True,
            "auto_apply_allowed": False,
        },
        {
            "schema_version": "OperatorReviewItem.v1",
            "review_id": "a",
            "created_at": "2026-01-01T00:00:00+00:00",
            "source_system": "calibration",
            "decision_type": "REQUEST_EVIDENCE",
            "priority": "P0",
            "reason": "r",
            "evidence_refs": [],
            "operator_required": True,
            "auto_apply_allowed": False,
        },
        {
            "schema_version": "OperatorReviewItem.v1",
            "review_id": "a",
            "created_at": "2026-01-01T00:00:00+00:00",
            "source_system": "fusion",
            "decision_type": "NO_ACTION",
            "priority": "P2",
            "reason": "r",
            "evidence_refs": [],
            "operator_required": True,
            "auto_apply_allowed": False,
        },
    ]
    queue = build_operator_queue(items)
    assert [item["priority"] for item in queue["items"]] == ["P0", "P1", "P2"]


def test_not_computable_propagation_to_p0_request_evidence():
    report = _report("NOT_COMPUTABLE")
    advisory = build_domain_weight_advisory(report)
    fusion = build_fusion_projection(report, advisory)
    items = build_review_items(report, advisory, fusion)
    assert any(item["decision_type"] == "REQUEST_EVIDENCE" and item["priority"] == "P0" for item in items)


class _Signal:
    def __init__(self, provenance_status: str = "complete", invariance_status: str = "pass"):
        self.provenance_status = provenance_status
        self.invariance_status = invariance_status


class _Run:
    def __init__(self, *, drift_class: str = "none", provenance_status: str = "complete"):
        self.session_active = True
        self.session_max_steps = 10
        self.session_steps_used = 0
        self.actions_remaining = 1
        self.signal = _Signal(provenance_status=provenance_status)
        self.stability_report = {"drift_class": drift_class}


def test_flow_exposes_operator_queue_without_execution_side_effects():
    run = _Run(drift_class="major", provenance_status="complete")
    output = build_calibration_drift_report(run, current_policy_hash="h1", write_ledger=False)
    assert "operator_queue" in output
    assert "operator_review_items" in output
    assert not hasattr(run, "executed_actions")
