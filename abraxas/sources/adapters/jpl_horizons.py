"""NASA JPL Horizons adapter (HTTP snapshot + cache fallback)."""

from __future__ import annotations

from abraxas.sources.adapters.http_snapshot import HTTPSnapshotAdapter


class JPLHorizonsAdapter(HTTPSnapshotAdapter):
    adapter_name = "jpl_horizons_api"
    version = "0.2"
