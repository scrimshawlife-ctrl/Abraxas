from __future__ import annotations

from abraxas.oracle.v2.orchestrate import attach_v2


def test_attach_v2_validates_by_default():
    env = {"oracle_signal": {"scores_v1": {"slang": {"top_risk": []}, "aalmanac": {"top_patterns": []}}}}
    out = attach_v2(envelope=env, config_hash="FIXED_CONFIG_HASH_0000000000000000", do_stabilization_tick=False)
    assert "v2" in out["oracle_signal"]
    assert out["oracle_signal"]["v2"]["mode"] == out["oracle_signal"]["v2"]["mode_decision"]["mode"]
