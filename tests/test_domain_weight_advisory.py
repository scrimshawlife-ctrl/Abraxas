from abx.weighting.advisory_builder import DEFAULT_WEIGHTS, build_domain_weight_advisory
from webpanel.gates import build_calibration_drift_report


def _base_report(status: str) -> dict:
    return {
        "schema_version": "CalibrationDriftReport.v1",
        "generated_at": "2026-01-01T00:00:00+00:00",
        "mean_brier": 0.0,
        "sample_size": 0,
        "not_computable_count": 0,
        "calibration_drift_status": status,
        "promotion_gate_status": "PASS",
        "dominant_failure_mode": "none",
        "evidence_refs": ["x"],
    }


def test_domain_weight_advisory_schema_and_normalization():
    advisory = build_domain_weight_advisory(_base_report("REVIEW_REQUIRED"))
    assert advisory["schema_version"] == "DomainWeightAdvisory.v1"
    assert set(advisory["base_weights"].keys()) == set(DEFAULT_WEIGHTS.keys())
    assert set(advisory["adjusted_weights"].keys()) == set(DEFAULT_WEIGHTS.keys())
    assert abs(sum(advisory["adjusted_weights"].values()) - 1.0) < 1e-12
    assert advisory["advisory_only"] is True


def test_not_computable_propagation_and_no_mutation():
    advisory = build_domain_weight_advisory(_base_report("NOT_COMPUTABLE"))
    assert advisory["adjustment_reason"] == "NOT_COMPUTABLE"
    assert advisory["confidence"] == 0.0
    assert advisory["adjusted_weights"] == DEFAULT_WEIGHTS


def test_deterministic_output_surface_excluding_time():
    advisory_a = build_domain_weight_advisory(_base_report("FAIL"))
    advisory_b = build_domain_weight_advisory(_base_report("FAIL"))
    for key in advisory_a:
        if key == "generated_at":
            continue
        assert advisory_a[key] == advisory_b[key]


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


def test_gates_flow_exposes_advisory_without_runtime_mutation():
    run = _Run(drift_class="major", provenance_status="complete")
    output = build_calibration_drift_report(run, current_policy_hash="h1", write_ledger=False)
    assert "domain_weight_advisory" in output
    advisory = output["domain_weight_advisory"]
    assert advisory["advisory_only"] is True
    assert advisory["adjustment_reason"] == "NOT_COMPUTABLE"
    assert not hasattr(run, "weights")


def test_confidence_decreases_with_higher_brier():
    low = build_domain_weight_advisory(_base_report("PASS") | {"mean_brier": 0.05, "sample_size": 10})
    high = build_domain_weight_advisory(_base_report("PASS") | {"mean_brier": 0.2, "sample_size": 10})
    assert low["confidence"] > high["confidence"]


def test_confidence_increases_with_sample_size():
    small = build_domain_weight_advisory(_base_report("PASS") | {"mean_brier": 0.05, "sample_size": 2})
    large = build_domain_weight_advisory(_base_report("PASS") | {"mean_brier": 0.05, "sample_size": 10})
    assert small["confidence"] < large["confidence"]


def test_pass_low_brier_small_sample_positive_not_max():
    advisory = build_domain_weight_advisory(_base_report("PASS") | {"mean_brier": 0.07333333333333333, "sample_size": 3})
    assert advisory["confidence"] > 0.0
    assert advisory["confidence"] < 1.0
