from __future__ import annotations

from abraxas_ase.provenance import stable_json_dumps
from abraxas_ase.runes.invoke import invoke_rune


def test_sdct_rune_determinism() -> None:
    items = [
        {
            "id": "1",
            "source": "alpha",
            "published_at": "2026-01-24T00:00:00Z",
            "title": "Sator Arepo",
            "text": "Tenet opera rotas.",
        },
        {
            "id": "2",
            "source": "beta",
            "published_at": "2026-01-24T00:10:00Z",
            "title": "Rotas Tenet",
            "text": "Arepo sator.",
        },
    ]
    payload = {
        "items": items,
        "date": "2026-01-24",
        "event_keys_by_item_id": {
            "1": "evt-alpha",
            "2": "evt-beta",
        },
    }
    ctx = {
        "run_id": "run-0001",
        "date": "2026-01-24",
        "runtime_lexicon_hash": "test-hash-123",
    }

    first = invoke_rune("sdct.text_subword.v1", payload, ctx)
    second = invoke_rune("sdct.text_subword.v1", payload, ctx)

    assert stable_json_dumps(first) == stable_json_dumps(second)
