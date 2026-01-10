from __future__ import annotations

from pathlib import Path

from abraxas.seeds.year_run import YearRunConfig, run_year


def test_year_run_emits_coverage(tmp_path: Path):
    out = tmp_path / "seedpack.json"
    cache = tmp_path / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    cfg = YearRunConfig(year=2025, window="weekly", out_path=out, cache_dir=cache, offline=True)
    sp = run_year(cfg)
    assert "coverage" in sp
    assert isinstance(sp["coverage"], list)
