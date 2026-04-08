from abraxas.oracle.mbom_v1 import assess_ambiguity


def test_mbom_assessment_non_authoritative_and_bounded():
    out = assess_ambiguity(
        lifecycle_states={"a": "SEED", "b": "STABLE", "c": "EMERGENT"},
        domain_signals=["x", "y"],
        resonance_score=0.45,
    ).to_dict()
    assert out["authority"] == "non-authoritative"
    assert out["lane"] == "support"
    assert 0.0 <= out["ambiguity_score"] <= 1.0


def test_mbom_band_transitions():
    low = assess_ambiguity(lifecycle_states={"a": "STABLE"}, domain_signals=[], resonance_score=0.0)
    high = assess_ambiguity(
        lifecycle_states={"a": "SEED", "b": "EMERGENT", "c": "DRIFT"},
        domain_signals=[str(i) for i in range(12)],
        resonance_score=1.0,
    )
    assert low.ambiguity_band == "LOW"
    assert high.ambiguity_band == "HIGH"
