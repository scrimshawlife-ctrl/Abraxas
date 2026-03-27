"""Unicode CLDR adapter (HTTP snapshot + cache fallback)."""

from __future__ import annotations

from abraxas.sources.adapters.http_snapshot import HTTPSnapshotAdapter


class CLDRSnapshotAdapter(HTTPSnapshotAdapter):
    adapter_name = "cldr_snapshot"
    version = "0.2"
