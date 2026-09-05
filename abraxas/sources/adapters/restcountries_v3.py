"""REST Countries v3 catalog adapter (HTTP snapshot + cache fallback)."""

from __future__ import annotations

from abraxas.sources.adapters.http_snapshot import HTTPSnapshotAdapter


class RESTCountriesV3Adapter(HTTPSnapshotAdapter):
    adapter_name = "restcountries_v3"
    version = "0.2"
