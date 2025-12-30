from __future__ import annotations

import pytest

from abraxas.oracle.v2.wire import build_v2_block
from abraxas.oracle.v2.validate import validate_v2_block, validate_envelope_v2, V2ValidationError


CFG = "FIXED_CONFIG_HASH_0000000000000000"


def _checks():
    return {
        "v1_golden_pass_rate": 1.0,
        "drift_budget_violations": 0,
        "evidence_bundle_overflow_rate": 0.0,
        "ci_volatility_correlation": 0.72,
        "interaction_noise_rate": 0.22,
    }


def _router_input():
    return {
        "max_band_width": 8,
        "max_MRS": 20,
        "negative_signal_alerts": 0,
        "thresholds": {"BW_HIGH": 20, "MRS_HIGH": 70},
    }


def test_validate_v2_block_ok():
    v2 = build_v2_block(checks=_checks(), router_input=_router_input(), config_hash=CFG)
    validate_v2_block(v2)


def test_validate_envelope_ok():
    v2 = build_v2_block(checks=_checks(), router_input=_router_input(), config_hash=CFG)
    env = {"oracle_signal": {"v2": v2}}
    validate_envelope_v2(env)


def test_validate_raises_on_mode_lock_violation():
    v2 = build_v2_block(checks=_checks(), router_input=_router_input(), config_hash=CFG)
    v2["mode"] = "ANALYST" if v2["mode"] != "ANALYST" else "SNAPSHOT"
    with pytest.raises(V2ValidationError):
        validate_v2_block(v2)


def test_validate_raises_on_bad_status():
    v2 = build_v2_block(checks=_checks(), router_input=_router_input(), config_hash=CFG)
    v2["compliance"]["status"] = "NOPE"
    with pytest.raises(V2ValidationError):
        validate_v2_block(v2)
