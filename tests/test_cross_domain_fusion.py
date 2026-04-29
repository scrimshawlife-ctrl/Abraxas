from abx.fusion.fusion_builder import build_fusion_projection
from abx.weighting.advisory_builder import build_domain_weight_advisory
from webpanel.gates import build_calibration_drift_report


def _calibration_report(status: str, generated_at: str = "2026-01-01T00:00:00+00:00") -> dict:
    return {
        "schema_version": "CalibrationDriftReport.v1",
        "generated_at": generated_at,
        "mean_brier": 0.0,
        "sample_size": 0,
        "not_computable_count": 0,
        "calibration_drift_status": status,
        "promotion_gate_status": "PASS",
        "dominant_failure_mode": "none",
        "evidence_refs": ["x"],
    }


def test_fusion_schema_and_bounded_priority():
    report = _calibration_report("REVIEW_REQUIRED")
    advisory = build_domain_weight_advisory(report)
    projection = build_fusion_projection(report, advisory)
    assert projection["schema_version"] == "CrossDomainFusionProjection.v1"
    assert projection["authority_effect"] == "ADVISORY_ONLY"
    assert 0.0 <= projection["fused_priority_score"] <= 1.0


def test_fusion_deterministic_surface_excluding_time():
    report = _calibration_report("FAIL")
    advisory = build_domain_weight_advisory(report)
    a = build_fusion_projection(report, advisory)
    b = build_fusion_projection(report, advisory)
    for key in a:
        if key == "generated_at":
            continue
        assert a[key] == b[key]


def test_fusion_not_computable_propagation():
    report = _calibration_report("NOT_COMPUTABLE")
    advisory = build_domain_weight_advisory(report)
    projection = build_fusion_projection(report, advisory)
    assert projection["fused_priority_score"] == 0.0
    assert "CALIBRATION_DRIFT" in projection["drift_alerts"]
    assert "LOW_CONFIDENCE" in projection["drift_alerts"]


def test_fusion_dominance_detection():
    report = _calibration_report("PASS")
    advisory = build_domain_weight_advisory(report)
    projection = build_fusion_projection(report, advisory)
    assert projection["dominant_domain"] == "market_pse"
    assert projection["dominance_ratio"] > 1.0


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


def test_gates_flow_exposes_fusion_without_runtime_mutation():
    run = _Run(drift_class="major", provenance_status="complete")
    output = build_calibration_drift_report(run, current_policy_hash="h1", write_ledger=False)
    assert "fusion_projection" in output
    projection = output["fusion_projection"]
    assert projection["authority_effect"] == "ADVISORY_ONLY"
    assert not hasattr(run, "weights")
