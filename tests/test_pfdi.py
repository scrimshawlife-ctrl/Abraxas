from __future__ import annotations

from abraxas_ase.engine import compute_pfdi
from abraxas_ase.types import SubAnagramHit


def test_pfdi_state_updates() -> None:
    items = [{"id":"1","source":"ap","url":"u","published_at":"x","title":"Test headline","text":"x"}]
    hits = [SubAnagramHit(token="ukraine", sub="nuke", tier=2, verified=True, item_id="1", source="ap", lane="core")]

    alerts, new_state, ledger = compute_pfdi(items, hits, pfdi_state={"version":1,"stats":{}}, key=None)
    assert "stats" in new_state
    assert len(ledger) == 1
