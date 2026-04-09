from abraxas.oracle.advisory.mircl_adapter import MirclAdapter


def test_mircl_not_computable_when_missing_observations() -> None:
    adapter = MirclAdapter()
    out = adapter.build(authority={}, normalized={"hashable_core": {"payload": {"observations": []}}})
    assert out["status"] == "NOT_COMPUTABLE"
    assert out["computable"] is False
    assert set(out["payload"].keys()) >= {
        "meaning_pressure",
        "narrative_instability",
        "perception_drift",
        "meaning_state_summary",
        "reality_state",
        "dominant_controller",
        "key_constraints",
    }
