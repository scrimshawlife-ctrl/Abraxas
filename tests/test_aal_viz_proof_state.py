from abx.fusion.fusion_builder import build_fusion_projection
from abx.operator.queue_builder import build_operator_queue
from abx.operator.review_builder import build_review_items
from abx.viz.proof_builder import build_proof_states
from abx.viz.set_builder import build_proof_state_set
from abx.weighting.advisory_builder import build_domain_weight_advisory
from webpanel.gates import build_calibration_drift_report


def _report(status: str, sha: str = "NOT_COMPUTABLE") -> dict:
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
        "sha256": sha,
    }


def test_schema_and_fail_closed_when_hash_missing():
    report = _report("PASS", sha="NOT_COMPUTABLE")
    advisory = build_domain_weight_advisory(report)
    advisory["sha256"] = "NOT_COMPUTABLE"
    fusion = build_fusion_projection(report, advisory)
    fusion["sha256"] = "NOT_COMPUTABLE"
    queue = build_operator_queue(build_review_items(report, advisory, fusion))
    states = build_proof_states(report, advisory, fusion, queue)
    assert all(state["schema_version"] == "AALVizProofState.v1" for state in states)
    assert all(state["fail_closed"] is True for state in states)
    assert all(state["display_allowed"] is False for state in states)


def test_authority_lane_mapping_and_shadow_never_forecast():
    report = _report("PASS", sha="abc")
    advisory = build_domain_weight_advisory(report)
    advisory["sha256"] = "def"
    fusion = build_fusion_projection(report, advisory)
    fusion["sha256"] = "ghi"
    queue = build_operator_queue(build_review_items(report, advisory, fusion))
    states = build_proof_states(report, advisory, fusion, queue)
    lane_by_id = {s["projection_id"]: s["authority_lane"] for s in states}
    assert lane_by_id["calibration_drift_report"] == "FORECAST"
    assert lane_by_id["domain_weight_advisory"] == "FORECAST"
    assert lane_by_id["fusion_projection"] == "PROJECTION"
    assert all(not (s["projection_id"] == "fusion_projection" and s["authority_lane"] == "FORECAST") for s in states)


def test_deterministic_ordering_and_set_aggregation():
    report = _report("FAIL", sha="a")
    advisory = build_domain_weight_advisory(report)
    advisory["sha256"] = "b"
    fusion = build_fusion_projection(report, advisory)
    fusion["sha256"] = "c"
    queue = build_operator_queue(build_review_items(report, advisory, fusion))
    states = build_proof_states(report, advisory, fusion, queue)
    state_set = build_proof_state_set(states)
    ids = [s["projection_id"] for s in state_set["items"]]
    assert ids == sorted(ids, key=lambda x: ({"calibration_drift_report": 0, "domain_weight_advisory": 1, "fusion_projection": 2}[x]))
    assert state_set["total_items"] == 3


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


def test_flow_exposes_proof_state_without_execution_paths():
    run = _Run(drift_class="major", provenance_status="complete")
    output = build_calibration_drift_report(run, current_policy_hash="h1", write_ledger=False)
    assert "proof_states" in output
    assert "proof_state_set" in output
    assert not hasattr(run, "executed_actions")
