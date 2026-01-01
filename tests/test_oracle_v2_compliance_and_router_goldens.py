from abraxas.oracle.v2.compliance import build_compliance_report
from abraxas.oracle.v2.mode_router import route_mode_v2


CFG = "FIXED_CONFIG_HASH_0000000000000000"


def test_compliance_green_all_ok():
    rep = build_compliance_report(
        checks={
            "v1_golden_pass_rate": 1.0,
            "drift_budget_violations": 0,
            "evidence_bundle_overflow_rate": 0.0,
            "ci_volatility_correlation": 0.72,
            "interaction_noise_rate": 0.22,
        },
        config_hash=CFG,
        date_iso="2025-12-28T00:00:00Z",
    )
    assert rep["status"] == "GREEN"


def test_compliance_red_on_drift():
    rep = build_compliance_report(
        checks={
            "v1_golden_pass_rate": 1.0,
            "drift_budget_violations": 1,
            "evidence_bundle_overflow_rate": 0.0,
            "ci_volatility_correlation": 0.72,
            "interaction_noise_rate": 0.22,
        },
        config_hash=CFG,
        date_iso="2025-12-28T00:00:00Z",
    )
    assert rep["status"] == "RED"


def test_router_user_override():
    out = route_mode_v2(
        {
            "user_mode_request": "RITUAL",
            "compliance_status": "RED",
            "max_band_width": 40,
            "max_MRS": 95,
            "negative_signal_alerts": 2,
            "thresholds": {"BW_HIGH": 20, "MRS_HIGH": 70},
            "config_hash": CFG,
        }
    )
    assert out["mode"] == "RITUAL"
    assert "USER_OVERRIDE" in out["reasons"]


def test_router_red_forces_analyst():
    out = route_mode_v2(
        {
            "compliance_status": "RED",
            "max_band_width": 5,
            "max_MRS": 10,
            "negative_signal_alerts": 0,
            "thresholds": {"BW_HIGH": 20, "MRS_HIGH": 70},
            "config_hash": CFG,
        }
    )
    assert out["mode"] == "ANALYST"
    assert "COMPLIANCE_RED" in out["reasons"]


def test_router_default_snapshot():
    out = route_mode_v2(
        {
            "compliance_status": "GREEN",
            "max_band_width": 8,
            "max_MRS": 20,
            "negative_signal_alerts": 0,
            "thresholds": {"BW_HIGH": 20, "MRS_HIGH": 70},
            "config_hash": CFG,
        }
    )
    assert out["mode"] == "SNAPSHOT"
