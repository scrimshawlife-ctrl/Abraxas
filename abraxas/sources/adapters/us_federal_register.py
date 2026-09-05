"""US Federal Register documents adapter (HTTP snapshot + cache fallback)."""

from __future__ import annotations

from abraxas.sources.adapters.http_snapshot import HTTPSnapshotAdapter


class USFederalRegisterAdapter(HTTPSnapshotAdapter):
    adapter_name = "us_federal_register"
    version = "0.2"
