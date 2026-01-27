from __future__ import annotations

from abraxas_ase.provenance import stable_json_dumps
from abraxas_ase.runes.invoke import invoke_rune


def test_square_rune_determinism() -> None:
    items = [
        {
            "id": "1",
            "source": "alpha",
            "published_at": "2026-01-24T00:00:00Z",
            "title": "Square 5x5",
            "text": "Alpha 123 beta 456",
        }
    ]
    payload = {
        "items": items,
        "date": "2026-01-24",
        "event_keys_by_item_id": {
            "1": "evt-alpha",
        },
    }
    ctx = {"run_id": "run-0004"}

    first = invoke_rune("sdct.square_constraints.v1", payload, ctx)
    second = invoke_rune("sdct.square_constraints.v1", payload, ctx)

    assert stable_json_dumps(first) == stable_json_dumps(second)
