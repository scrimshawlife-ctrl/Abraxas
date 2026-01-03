"""Deterministic CSV adapter parsing."""

from __future__ import annotations

from pathlib import Path

from abraxas.sources.adapters.timeseries_csv import TimeSeriesCSVAdapter
from abraxas.sources.atlas import get_source
from abraxas.sources.types import SourceWindow


def test_timeseries_csv_parse(tmp_path: Path):
    csv_path = tmp_path / "series.csv"
    csv_path.write_text("ts,value,unit,series_id\n2025-01-01T00:00:00Z,100.0,index,cpi\n2025-02-01T00:00:00Z,101.0,index,cpi\n")

    adapter = TimeSeriesCSVAdapter()
    source_spec = get_source("NOAA_NCEI_CDO_V2")
    assert source_spec is not None
    window = SourceWindow(start_utc="2025-01-01T00:00:00Z", end_utc="2025-02-01T00:00:00Z")

    packets = adapter.fetch_parse_emit(
        source_spec=source_spec,
        window=window,
        params={"path": str(csv_path)},
        cache_dir=None,
        run_ctx={},
    )
    assert packets[0].payload["series"][0]["value"] == 100.0
