from __future__ import annotations

import os
import tempfile

from abraxas.oracle.v2.orchestrate import attach_v2


CFG = "FIXED_CONFIG_HASH_0000000000000000"


def _base_envelope():
    return {
        "oracle_signal": {
            "scores_v1": {
                "slang": {
                    "top_risk": [{"term": "ghostmode", "MRS": 37.63}],
                    "top_vital": [{"term": "ghostmode", "SVS": 85.56}],
                },
                "aalmanac": {"top_patterns": []},
            }
        }
    }


def test_attach_v2_adds_v2_block_and_ticks_ledger():
    env = _base_envelope()
    with tempfile.TemporaryDirectory() as td:
        ledger = os.path.join(td, "oracle_v2.jsonl")
        out = attach_v2(
            envelope=env,
            config_hash=CFG,
            do_stabilization_tick=True,
            ledger_path=ledger,
            date_iso="2025-12-28T00:00:00Z",
        )
        assert "v2" in out["oracle_signal"]
        assert out["oracle_signal"]["v2"]["mode"] == out["oracle_signal"]["v2"]["mode_decision"]["mode"]
        # ledger should have 1 line
        with open(ledger, "r", encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) == 1


def test_attach_v2_respects_user_mode_request():
    env = _base_envelope()
    out = attach_v2(
        envelope=env,
        config_hash=CFG,
        user_mode_request="RITUAL",
        do_stabilization_tick=False,
        date_iso="2025-12-28T00:00:00Z",
    )
    assert out["oracle_signal"]["v2"]["mode"] == "RITUAL"
    assert "USER_OVERRIDE" in out["oracle_signal"]["v2"]["mode_decision"]["reasons"]
