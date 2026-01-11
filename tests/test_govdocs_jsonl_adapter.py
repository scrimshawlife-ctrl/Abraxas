"""Deterministic governance JSONL adapter parsing."""

from __future__ import annotations

from pathlib import Path

from abraxas.sources.adapters.govdocs_jsonl import GovDocsJSONLAdapter
from abraxas.sources.atlas import get_source
from abraxas.sources.types import SourceWindow


def test_govdocs_jsonl_parse(tmp_path: Path):
    jsonl_path = tmp_path / "docs.jsonl"
    jsonl_path.write_text("{\"ts\":\"2025-01-01T00:00:00Z\",\"title\":\"Policy\",\"text\":\"Update\"}\n")

    adapter = GovDocsJSONLAdapter()
    source_spec = get_source("NOAA_NCEI_CDO_V2")
    assert source_spec is not None
    window = SourceWindow(start_utc="2025-01-01T00:00:00Z", end_utc="2025-01-01T01:00:00Z")

    packets = adapter.fetch_parse_emit(
        source_spec=source_spec,
        window=window,
        params={"path": str(jsonl_path)},
        cache_dir=None,
        run_ctx={},
    )
    assert packets[0].payload["documents"][0]["title"] == "Policy"
