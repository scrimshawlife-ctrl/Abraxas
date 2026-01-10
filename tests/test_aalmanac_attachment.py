from abraxas.attachments.aalmanac_v1 import AALmanacConfig, build_aalmanac_attachment


def test_aalmanac_enforces_single_vs_compound_contract() -> None:
    seed_inputs = {"a": 1}
    raw = [
        {"term": "two words", "term_type": "single", "tokens": ["two", "words"], "domain_tags": ["culture"]},
        {
            "term": "ghost",
            "domain_tags": ["culture"],
            "usage_frame": "x" * 20,
            "example_templates": ["x" * 12],
            "scores": {"STI": 0.2, "CP": 0.2, "IPS": 0.2, "RFR": 0.2, "lambdaN": 0.2},
            "confidence": 0.6,
            "half_life": "weeks",
        },
        {
            "term": "rent-paying",
            "domain_tags": ["tech"],
            "usage_frame": "x" * 20,
            "example_templates": ["x" * 12],
            "scores": {"STI": 0.2, "CP": 0.2, "IPS": 0.2, "RFR": 0.2, "lambdaN": 0.2},
            "confidence": 0.6,
            "half_life": "weeks",
        },
    ]
    out = build_aalmanac_attachment(seed_inputs=seed_inputs, raw_terms=raw, cfg=AALmanacConfig(max_entries=50))
    terms = [e["term"] for e in out["entries"]]
    assert "two words" not in terms
    assert "ghost" in terms
    assert "rent-paying" in terms


def test_aalmanac_determinism_hash_stable_given_same_inputs_and_terms() -> None:
    seed_inputs = {"a": 1, "b": 2}
    raw = [
        {
            "term": "ghost",
            "domain_tags": ["culture"],
            "usage_frame": "x" * 20,
            "example_templates": ["x" * 12],
            "scores": {"STI": 0.2, "CP": 0.2, "IPS": 0.2, "RFR": 0.2, "lambdaN": 0.2},
            "confidence": 0.6,
            "half_life": "weeks",
        },
        {
            "term": "rent-paying",
            "domain_tags": ["tech"],
            "usage_frame": "x" * 20,
            "example_templates": ["x" * 12],
            "scores": {"STI": 0.2, "CP": 0.2, "IPS": 0.2, "RFR": 0.2, "lambdaN": 0.2},
            "confidence": 0.6,
            "half_life": "weeks",
        },
    ]
    cfg = AALmanacConfig(max_entries=50)
    o1 = build_aalmanac_attachment(seed_inputs=seed_inputs, raw_terms=raw, cfg=cfg)
    o2 = build_aalmanac_attachment(seed_inputs=seed_inputs, raw_terms=raw, cfg=cfg)
    # determinism_hash should match aside from generated_at_utc/run_id changing.
    # We compare entry ordering + inputs_hash + terms and scores.
    assert o1["inputs_hash"] == o2["inputs_hash"]
    assert [e["term"] for e in o1["entries"]] == [e["term"] for e in o2["entries"]]
    assert [e["scores"] for e in o1["entries"]] == [e["scores"] for e in o2["entries"]]
