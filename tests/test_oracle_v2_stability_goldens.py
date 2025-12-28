from __future__ import annotations

import copy

from abraxas.oracle.v2.guard import assert_mode_lock
from abraxas.oracle.v2.wire import build_v2_block


CFG = "FIXED_CONFIG_HASH_0000000000000000"


def _base_checks():
    return {
        "v1_golden_pass_rate": 1.0,
        "drift_budget_violations": 0,
        "evidence_bundle_overflow_rate": 0.0,
        "ci_volatility_correlation": 0.72,
        "interaction_noise_rate": 0.22,
    }


def _base_router_input():
    return {
        # NOTE: compliance_status injected inside build_v2_block
        "max_band_width": 8,
        "max_MRS": 20,
        "negative_signal_alerts": 0,
        "thresholds": {"BW_HIGH": 20, "MRS_HIGH": 70},
    }


def test_mode_decision_fingerprint_stable_identical_inputs():
    checks = _base_checks()
    ri = _base_router_input()

    a = build_v2_block(checks=checks, router_input=ri, config_hash=CFG)
    b = build_v2_block(checks=copy.deepcopy(checks), router_input=copy.deepcopy(ri), config_hash=CFG)

    assert a["mode"] == b["mode"]
    assert a["mode_decision"]["reasons"] == b["mode_decision"]["reasons"]
    assert a["mode_decision"]["fingerprint"] == b["mode_decision"]["fingerprint"]
    assert_mode_lock(a)
    assert_mode_lock(b)


def test_mode_decision_changes_when_user_override_changes():
    checks = _base_checks()
    ri = _base_router_input()

    a = build_v2_block(checks=checks, router_input=ri, config_hash=CFG)

    ri2 = copy.deepcopy(ri)
    ri2["user_mode_request"] = "RITUAL"
    b = build_v2_block(checks=checks, router_input=ri2, config_hash=CFG)

    assert a["mode"] != b["mode"]
    assert a["mode_decision"]["fingerprint"] != b["mode_decision"]["fingerprint"]
    assert_mode_lock(a)
    assert_mode_lock(b)


def test_mode_lock_guard_raises_on_violation():
    checks = _base_checks()
    ri = _base_router_input()
    v2 = build_v2_block(checks=checks, router_input=ri, config_hash=CFG)

    # Simulate an illegal divergence
    v2["mode"] = "ANALYST" if v2["mode"] != "ANALYST" else "SNAPSHOT"
    raised = False
    try:
        assert_mode_lock(v2)
    except ValueError:
        raised = True
    assert raised is True
