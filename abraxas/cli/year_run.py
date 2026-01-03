"""CLI for year-run seedpack v0.2."""

from __future__ import annotations

from pathlib import Path

from abraxas.seeds.year_run import YearRunConfig, run_year


def run_year_cmd(
    year: int,
    window: str,
    out: str,
    cache_dir: str,
    offline: bool,
    include_linguistic: bool,
    include_economics: bool,
    include_governance: bool,
    allow_simulated: bool,
) -> int:
    config = YearRunConfig(
        year=year,
        window=window,
        out_path=Path(out),
        cache_dir=Path(cache_dir),
        offline=offline,
        include_linguistic=include_linguistic,
        include_economics=include_economics,
        include_governance=include_governance,
        allow_simulated=allow_simulated,
    )
    run_year(config)
    return 0
