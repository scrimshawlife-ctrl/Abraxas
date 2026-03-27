"""Tomsk SOS adapter (HTTP snapshot + cache fallback)."""

from __future__ import annotations

from abraxas.sources.adapters.http_snapshot import HTTPSnapshotAdapter


class TomskSOSAdapter(HTTPSnapshotAdapter):
    adapter_name = "tomsk_sos_scrape_cache"
    version = "0.2"
