"""Unicode CLDR adapter (cache-only stub)."""

from __future__ import annotations

from abraxas.sources.adapters.cache_only_stub import CacheOnlyAdapter


class CLDRSnapshotAdapter(CacheOnlyAdapter):
    adapter_name = "cldr_snapshot"
    version = "0.1"
