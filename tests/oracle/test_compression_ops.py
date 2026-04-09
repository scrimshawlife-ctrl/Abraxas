from abraxas.oracle.runtime.compression_ops import bound_evidence_v0, compress_signal_v0, dedupe_signal_items_v0


def test_compression_and_dedupe_deterministic() -> None:
    obs = [
        {"domain": "a", "subdomain": "x", "score": 0.3, "confidence": 0.5, "age_hours": 1, "evidence_refs": ["e2", "e1"]},
        {"domain": "a", "subdomain": "x", "score": 0.7, "confidence": 0.7, "age_hours": 2, "evidence_refs": ["e3"]},
    ]
    comp = compress_signal_v0(obs)
    ded = dedupe_signal_items_v0(comp)
    assert len(comp) == 1
    assert len(ded) == 1
    assert bound_evidence_v0(["b", "a", "a"]) == ["a", "b"]
