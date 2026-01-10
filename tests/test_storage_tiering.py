from __future__ import annotations

from abraxas.policy.utp import load_active_utp
from abraxas.storage.index import StorageIndexEntry
from abraxas.storage.lifecycle_ir import default_lifecycle_ir
from abraxas.storage.tiering import assign_tier


def test_assign_tier_deterministic() -> None:
    ir = default_lifecycle_ir("2026-01-10T00:00:00Z", load_active_utp())
    entry = StorageIndexEntry(
        artifact_type="parsed",
        source_id="TEST",
        created_at_utc="2026-01-01T00:00:00Z",
        size_bytes=100,
        codec="lz4",
        tier="hot",
        path="/tmp/parsed.json",
        content_hash="hash",
    )
    tier_first = assign_tier(entry, ir, "2026-01-10T00:00:00Z")
    tier_second = assign_tier(entry, ir, "2026-01-10T00:00:00Z")
    assert tier_first == tier_second
    assert tier_first in {"cold", "deep_archive", "hot"}
