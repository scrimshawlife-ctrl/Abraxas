"""NIST bulletins adapter (HTTP snapshot + cache fallback)."""

from __future__ import annotations

from abraxas.sources.adapters.http_snapshot import HTTPSnapshotAdapter


class NISTBulletinsAdapter(HTTPSnapshotAdapter):
    adapter_name = "nist_bulletin_pdf_index"
    version = "0.2"
