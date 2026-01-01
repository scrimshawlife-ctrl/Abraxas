from __future__ import annotations

import os
import tempfile

from abraxas.oracle.v2.wire import build_v2_block
from abraxas.oracle.v2.stabilization import stabilization_tick, count_lines


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


def test_stabilization_tick_appends_and_increments_day():
    v2 = build_v2_block(checks=_checks(), router_input=_router_input(), config_hash=CFG)

    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "oracle_v2.jsonl")

        assert count_lines(path) == 0
        r1 = stabilization_tick(v2_block=v2, ledger_path=path, date_iso="2025-12-28T00:00:00Z")
        assert r1["day"] == 1
        assert count_lines(path) == 1

        r2 = stabilization_tick(v2_block=v2, ledger_path=path, date_iso="2025-12-29T00:00:00Z")
        assert r2["day"] == 2
        assert count_lines(path) == 2


def test_stabilization_row_contains_mode_and_fingerprint():
    v2 = build_v2_block(checks=_checks(), router_input=_router_input(), config_hash=CFG)

    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "oracle_v2.jsonl")
        r1 = stabilization_tick(v2_block=v2, ledger_path=path, date_iso="2025-12-28T00:00:00Z")

        assert r1["mode"] in ("SNAPSHOT", "ANALYST", "RITUAL")
        assert isinstance(r1["mode_decision_fingerprint"], str)
        assert len(r1["mode_decision_fingerprint"]) >= 16
        assert r1["provenance"]["config_hash"] == CFG
