"""NOAA SWPC Kp adapter (cache-only stub)."""

from __future__ import annotations

from abraxas.sources.adapters.cache_only_stub import CacheOnlyAdapter


class SWPCKpAdapter(CacheOnlyAdapter):
    adapter_name = "swpc_kp_json"
    version = "0.1"
