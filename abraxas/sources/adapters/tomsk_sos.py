"""Tomsk SOS adapter (cache-only stub)."""

from __future__ import annotations

from abraxas.sources.adapters.cache_only_stub import CacheOnlyAdapter


class TomskSOSAdapter(CacheOnlyAdapter):
    adapter_name = "tomsk_sos_scrape_cache"
    version = "0.1"
