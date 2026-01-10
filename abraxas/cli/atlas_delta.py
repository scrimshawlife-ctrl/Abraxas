"""Delta atlas CLI."""

from __future__ import annotations

import json
from pathlib import Path

from abraxas.atlas.compare import build_delta_pack
from abraxas.atlas.construct import load_seedpack
from abraxas.atlas.delta_export import export_delta_json, export_delta_trendpack


def run_atlas_delta_cmd(
    base_path: str,
    compare_path: str,
    out_path: str,
    comparison_label: str,
    trendpack_path: str | None = None,
) -> int:
    base_atlas = load_seedpack(Path(base_path))
    compare_atlas = load_seedpack(Path(compare_path))
    delta_pack = build_delta_pack(
        base_atlas,
        compare_atlas,
        comparison_label=comparison_label,
    )
    export_delta_json(delta_pack, Path(out_path))

    if trendpack_path:
        trendpack = export_delta_trendpack(delta_pack)
        out_file = Path(trendpack_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(trendpack, indent=2, sort_keys=True), encoding="utf-8")
    return 0
