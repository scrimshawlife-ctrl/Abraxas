# tests/test_transparency.py
from abraxas.linguistic.transparency import token_transparency_heuristic, TransparencyLexicon

def test_sti_range():
    assert 0.0 <= token_transparency_heuristic("aphex") <= 1.0
    assert 0.0 <= token_transparency_heuristic("apex") <= 1.0

def test_lexicon_provenance_stable():
    lex = TransparencyLexicon.build(["aphex twin", "apex twin"])
    assert len(lex.provenance_sha256) == 64
