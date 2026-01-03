"""NIST bulletins adapter (cache-only stub)."""

from __future__ import annotations

from abraxas.sources.adapters.cache_only_stub import CacheOnlyAdapter


class NISTBulletinsAdapter(CacheOnlyAdapter):
    adapter_name = "nist_bulletin_pdf_index"
    version = "0.1"
