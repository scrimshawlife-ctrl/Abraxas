from __future__ import annotations

from abraxas_ase.provenance import stable_json_dumps
from abraxas_ase.runes.invoke import invoke_rune


def test_digit_motif_rune_determinism() -> None:
    items = [
        {
            "id": "1",
            "source": "alpha",
            "published_at": "2026-01-24T00:00:00Z",
            "title": "UFC 311",
            "text": "UFC 311 at 7-11 on 2026-01-24",
        }
    ]
    payload = {
        "items": items,
        "date": "2026-01-24",
        "event_keys_by_item_id": {
            "1": "evt-alpha",
        },
    }
    ctx = {"run_id": "run-0002"}

    first = invoke_rune("sdct.digit_motif.v1", payload, ctx)
    second = invoke_rune("sdct.digit_motif.v1", payload, ctx)

    assert stable_json_dumps(first) == stable_json_dumps(second)
