"""USGS FDSN earthquake GeoJSON adapter (HTTP snapshot + cache fallback)."""

from __future__ import annotations

from abraxas.sources.adapters.http_snapshot import HTTPSnapshotAdapter


class USGSEarthquakeFDSNAdapter(HTTPSnapshotAdapter):
    adapter_name = "usgs_earthquake_fdsn"
    version = "0.2"
