from abraxas.detectors.shadow.anagram import detect_shadow_anagrams, AnagramConfig, AnagramBudgets


def test_shadow_anagram_is_deterministic_and_budgeted():
    cfg = AnagramConfig(budgets=AnagramBudgets(
        max_token_len=24,
        max_candidates_per_token=5,
        max_states=5_000,
        max_words_per_phrase=2,
    ))
    tokens = ["Signal Layer", "Slang Drift", "ABRAXAS", "zzzzzzzzzzzzzzzzzzzzzzzzzz"]  # last too long after norm
    out1 = detect_shadow_anagrams(tokens, context={"domain": "culture_memes", "subdomain": "slang_language_drift"}, config=cfg)
    out2 = detect_shadow_anagrams(tokens, context={"domain": "culture_memes", "subdomain": "slang_language_drift"}, config=cfg)
    assert out1["shadow_anagram_v1"]["artifact_hash"] == out2["shadow_anagram_v1"]["artifact_hash"]
    assert isinstance(out1["shadow_anagram_v1"]["candidates"], list)


def test_shadow_anagram_evidence_gating():
    tokens = ["Signal Layer"]
    out_no = detect_shadow_anagrams(tokens)
    assert "evidence_refs" not in out_no["shadow_anagram_v1"]
    for c in out_no["shadow_anagram_v1"]["candidates"]:
        assert "evidence_refs" not in c

    out_yes = detect_shadow_anagrams(tokens, evidence_refs=["ref:1", "ref:2"])
    assert "evidence_refs" in out_yes["shadow_anagram_v1"]
    for c in out_yes["shadow_anagram_v1"]["candidates"]:
        # candidates only include evidence_refs when there is evidence
        assert "evidence_refs" in c
