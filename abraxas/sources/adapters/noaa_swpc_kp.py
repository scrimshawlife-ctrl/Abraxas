"""NOAA SWPC Kp adapter (HTTP snapshot + cache fallback)."""

from __future__ import annotations

from abraxas.sources.adapters.http_snapshot import HTTPSnapshotAdapter


class SWPCKpAdapter(HTTPSnapshotAdapter):
    adapter_name = "swpc_kp_json"
    version = "0.2"
