"""NOAA NCEI CDO adapter (HTTP snapshot + cache fallback)."""

from __future__ import annotations

from abraxas.sources.adapters.http_snapshot import HTTPSnapshotAdapter


class NCEICDOAdapter(HTTPSnapshotAdapter):
    adapter_name = "ncei_cdo_v2"
    version = "0.2"
