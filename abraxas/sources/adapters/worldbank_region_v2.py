"""World Bank region catalog adapter (HTTP snapshot + cache fallback)."""

from __future__ import annotations

from abraxas.sources.adapters.http_snapshot import HTTPSnapshotAdapter


class WorldBankRegionV2Adapter(HTTPSnapshotAdapter):
    adapter_name = "worldbank_region_v2"
    version = "0.2"
