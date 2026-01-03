"""Atlas export CLI."""

from __future__ import annotations

import json
from pathlib import Path

from abraxas.atlas.construct import build_atlas_pack, load_seedpack
from abraxas.atlas.export import export_chronoscope, export_json, export_trendpack


def run_atlas_cmd(
    year: int,
    window: str,
    seed_path: str,
    out_path: str,
    trendpack_path: str | None = None,
    chronoscope_path: str | None = None,
) -> int:
    seedpack = load_seedpack(Path(seed_path))
    seed_year = int(seedpack.get("year") or 0)
    if seed_year and seed_year != year:
        raise SystemExit(f"Seedpack year {seed_year} does not match requested year {year}")
    atlas_pack = build_atlas_pack(seedpack, window_granularity=window)

    export_json(atlas_pack, Path(out_path))

    if trendpack_path:
        trendpack = export_trendpack(atlas_pack)
        Path(trendpack_path).parent.mkdir(parents=True, exist_ok=True)
        Path(trendpack_path).write_text(json.dumps(trendpack, indent=2, sort_keys=True), encoding="utf-8")
    if chronoscope_path:
        chronoscope = export_chronoscope(atlas_pack)
        Path(chronoscope_path).parent.mkdir(parents=True, exist_ok=True)
        Path(chronoscope_path).write_text(json.dumps(chronoscope, indent=2, sort_keys=True), encoding="utf-8")
    return 0
