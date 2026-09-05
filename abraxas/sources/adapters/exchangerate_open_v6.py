"""Open ExchangeRate API latest-USD adapter (HTTP snapshot + cache fallback)."""

from __future__ import annotations

from abraxas.sources.adapters.http_snapshot import HTTPSnapshotAdapter


class ExchangeRateOpenV6Adapter(HTTPSnapshotAdapter):
    adapter_name = "exchangerate_open_v6"
    version = "0.2"
