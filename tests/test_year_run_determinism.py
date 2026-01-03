"""Determinism tests for year-run seedpack v0.2."""

from __future__ import annotations

import hashlib
from pathlib import Path

from abraxas.seeds.year_run import YearRunConfig, run_year


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_year_run_deterministic(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    packet = {
        "source_id": "NOAA_SWPC_PLANETARY_KP",
        "observed_at_utc": "2025-01-01T00:00:00Z",
        "window_start_utc": "2025-01-01T00:00:00Z",
        "window_end_utc": "2025-01-01T01:00:00Z",
        "payload": {"kp_value": 3.0},
        "provenance": {},
    }
    (cache_dir / "packet.json").write_text(
        __import__("json").dumps(packet, sort_keys=True),
        encoding="utf-8",
    )

    out1 = tmp_path / "seed1.json"
    out2 = tmp_path / "seed2.json"

    config1 = YearRunConfig(year=2025, window="weekly", out_path=out1, cache_dir=cache_dir, offline=True)
    config2 = YearRunConfig(year=2025, window="weekly", out_path=out2, cache_dir=cache_dir, offline=True)

    run_year(config1)
    run_year(config2)

    assert _hash_file(out1) == _hash_file(out2)
