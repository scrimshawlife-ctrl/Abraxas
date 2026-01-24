from __future__ import annotations

from abraxas_ase.lexicon import build_default_lexicon
from abraxas_ase.engine import build_token_records


def test_token_records_basic() -> None:
    lex = build_default_lexicon()
    items = [{"id":"1","source":"ap","url":"u","published_at":"x","title":"Minneapolis ICE shooting","text":"Protest planned in Minnesota."}]
    recs = build_token_records(items, lex=lex, min_len=4)
    assert any(r.norm == "minneapolis" for r in recs)
    assert any(r.norm == "minnesota" for r in recs)
