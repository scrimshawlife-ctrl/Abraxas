"""NASA JPL Horizons adapter (cache-only stub)."""

from __future__ import annotations

from abraxas.sources.adapters.cache_only_stub import CacheOnlyAdapter


class JPLHorizonsAdapter(CacheOnlyAdapter):
    adapter_name = "jpl_horizons_api"
    version = "0.1"
