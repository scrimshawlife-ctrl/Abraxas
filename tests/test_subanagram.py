from __future__ import annotations

from abraxas_ase.lexicon import build_default_lexicon
from abraxas_ase.engine import build_token_records, tier2_subanagrams


def test_subanagram_ukraine_nuke() -> None:
    lex = build_default_lexicon()
    items = [{"id":"1","source":"r","url":"u","published_at":"x","title":"Ukraine update","text":"Ukraine"}]
    recs = build_token_records(items, lex=lex, min_len=4)
    hits = tier2_subanagrams(recs, lex=lex, min_sub_len=3, canary_subwords=None)
    assert any(h.token == "ukraine" and h.sub == "nuke" for h in hits)
