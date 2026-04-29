from abx.calibration.report_builder import build_calibration_report
from webpanel.gates import build_calibration_drift_report


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


def test_calibration_report_schema_and_deterministic_surface():
    report_a = build_calibration_report(
        drift_metrics={"mean_brier": 0.07, "sample_size": 3, "not_computable_count": 1},
        gate_state={"promotion_gate_status": "PASS"},
        evidence_refs=["x"],
    )
    report_b = build_calibration_report(
        drift_metrics={"mean_brier": 0.07, "sample_size": 3, "not_computable_count": 1},
        gate_state={"promotion_gate_status": "PASS"},
        evidence_refs=["x"],
    )

    assert report_a["schema_version"] == "CalibrationDriftReport.v1"
    assert report_a["calibration_drift_status"] == "PASS"
    assert report_a["promotion_gate_status"] == "PASS"
    assert report_a["evidence_refs"] == report_b["evidence_refs"]


def test_calibration_report_sample_size_under_three_review_required():
    report = build_calibration_report(
        drift_metrics={"mean_brier": 0.05, "sample_size": 2, "not_computable_count": 0},
        gate_state={"promotion_gate_status": "BLOCKED"},
        evidence_refs=["x"],
    )
    assert report["calibration_drift_status"] == "REVIEW_REQUIRED"


def test_calibration_report_missing_metrics_not_computable():
    report = build_calibration_report(
        drift_metrics={"mean_brier": 0.0, "sample_size": 0, "not_computable_count": 0},
        gate_state={"promotion_gate_status": "PASS"},
        evidence_refs=["x"],
    )
    assert report["calibration_drift_status"] == "NOT_COMPUTABLE"


def test_calibration_report_blocked_from_drift_gate():
    run = _Run(drift_class="major", provenance_status="complete")
    report = build_calibration_drift_report(run, current_policy_hash="h1", write_ledger=False)["report"]
    assert report["promotion_gate_status"] == "BLOCKED"
    assert report["dominant_failure_mode"] == "drift_blocked"
