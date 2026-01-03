"""NOAA NCEI CDO adapter (cache-only stub)."""

from __future__ import annotations

from abraxas.sources.adapters.cache_only_stub import CacheOnlyAdapter


class NCEICDOAdapter(CacheOnlyAdapter):
    adapter_name = "ncei_cdo_v2"
    version = "0.1"
