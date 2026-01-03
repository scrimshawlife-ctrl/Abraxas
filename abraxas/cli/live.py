"""Live atlas CLI."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from abraxas.live.export import export_latest_snapshot, export_live_json, export_live_trendpack
from abraxas.live.run import LiveRunContext, run_live_atlas
from abraxas.live.windowing import LiveWindowConfig


def run_live_cmd(
    window_size: str,
    step_size: str,
    retention: int,
    out_path: str,
    cache_dir: str,
    now_utc: str | None = None,
    snapshot_only: bool = False,
    trendpack_path: str | None = None,
) -> int:
    if now_utc is None:
        now_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    run_ctx = LiveRunContext(run_id=f"live_{now_utc}", now_utc=now_utc)
    window_config = LiveWindowConfig(
        window_size=window_size,
        step_size=step_size,
        retention=retention,
    )
    live_pack = run_live_atlas(
        sources=None,
        window_config=window_config,
        run_ctx=run_ctx,
        cache_dir=Path(cache_dir),
    )

    if snapshot_only:
        snapshot = export_latest_snapshot(live_pack)
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
        return 0

    export_live_json(live_pack, Path(out_path))

    if trendpack_path:
        trendpack = export_live_trendpack(live_pack)
        out_file = Path(trendpack_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(trendpack, indent=2, sort_keys=True), encoding="utf-8")
    return 0
