# tests/test_similarity.py
from abraxas.linguistic.similarity import normalized_edit_similarity, phonetic_similarity, intent_preservation_score

def test_edit_similarity_bounds():
    assert 0.0 <= normalized_edit_similarity("a", "b") <= 1.0
    assert normalized_edit_similarity("same", "same") == 1.0

def test_phonetic_similarity_basic():
    assert phonetic_similarity("aphex twin", "aphex twins") >= 0.75

def test_intent_score_deterministic():
    a = "in the nick of time we made it"
    b = "in the nit of time we made it"
    s1 = intent_preservation_score(a, b)
    s2 = intent_preservation_score(a, b)
    assert s1 == s2
    assert 0.0 <= s1 <= 1.0
