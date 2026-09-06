"""DE-LU Energy Charts + TimesFM 2.5 CPU smoke. Optional weights."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from abraxas.sources.adapters.http_snapshot import HTTPSnapshotAdapter
from abraxas.sources.adapters.timesfm_local import TimesFMLocalAdapter
from abraxas.sources.timesfm_shadow.constants import (
    BZN,
    DEFAULT_HORIZON,
    DEFAULT_OUT_DIR,
    DEFAULT_SEED,
    DEFAULT_TIMEOUT_S,
    DEFAULT_WINDOW_N,
    ENERGY_CHARTS_PRICE_URL,
    HF_REVISION,
    SOURCE_ID,
)
from abraxas.sources.timesfm_shadow.energy_charts import parse_energy_charts_price
from abraxas.sources.timesfm_shadow.infer import InferFn
from abraxas.sources.timesfm_shadow.packets import TimesFMShadowForecastV0, assert_shadow_locks
from abraxas.sources.timesfm_shadow.sink import write_shadow_packet
from abraxas.sources.types import SourceWindow


def run_de_lu_smoke(
    *,
    out_dir: Path,
    horizon: int = DEFAULT_HORIZON,
    seed: int = DEFAULT_SEED,
    hf_revision: str = HF_REVISION,
    window_n: int = DEFAULT_WINDOW_N,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    cache_dir: Path | None = None,
    url: str = ENERGY_CHARTS_PRICE_URL,
    infer_fn: InferFn | None = None,
) -> TimesFMShadowForecastV0:
    raw_payload = _fetch_price_payload(url=url, timeout_s=timeout_s, cache_dir=cache_dir)
    history = parse_energy_charts_price(raw_payload, window_n=window_n, bzn=BZN)
    packet = TimesFMLocalAdapter().predict(
        history,
        horizon=horizon,
        seed=seed,
        hf_revision=hf_revision,
        infer_fn=infer_fn,
    )
    assert_shadow_locks(packet)
    if packet.source_id != SOURCE_ID:
        raise ValueError("smoke packet source_id lock failed")
    write_shadow_packet(packet, out_dir)
    return packet


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m abraxas.sources.timesfm_shadow",
        description=(
            "Shadow-only TimesFM 2.5 DE-LU smoke. Writes local JSON under "
            "out/timesfm_shadow/. Does not mint Canon or Forecast."
        ),
    )
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--horizon", type=int, default=DEFAULT_HORIZON)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--hf-revision", default=HF_REVISION)
    parser.add_argument("--window-n", type=int, default=DEFAULT_WINDOW_N)
    parser.add_argument("--timeout-s", type=int, default=DEFAULT_TIMEOUT_S)
    parser.add_argument("--cache-dir", default="")
    parser.add_argument("--url", default=ENERGY_CHARTS_PRICE_URL)
    args = parser.parse_args(list(argv) if argv is not None else None)
    cache_dir = Path(args.cache_dir) if str(args.cache_dir).strip() else None
    try:
        packet = run_de_lu_smoke(
            out_dir=Path(args.out_dir),
            horizon=args.horizon,
            seed=args.seed,
            hf_revision=args.hf_revision,
            window_n=args.window_n,
            timeout_s=args.timeout_s,
            cache_dir=cache_dir,
            url=args.url,
        )
    except Exception as exc:
        sys.stderr.write(f"timesfm_shadow_smoke: blocked: {exc}\n")
        return 2
    sys.stdout.write(f"timesfm_shadow_smoke: wrote {packet.packet_hash()}\n")
    return 0


def _fetch_price_payload(
    *,
    url: str,
    timeout_s: int,
    cache_dir: Path | None,
) -> dict[str, object]:
    adapter = HTTPSnapshotAdapter()
    window = SourceWindow(start_utc="1970-01-01T00:00:00Z", end_utc="1970-01-01T00:00:00Z")
    raw = adapter.fetch(
        window,
        {"url": url, "timeout_s": timeout_s},
        cache_dir,
        {"run_id": "timesfm_shadow_smoke"},
    )
    parsed = adapter.parse(raw, run_ctx={"run_id": "timesfm_shadow_smoke"})
    if not isinstance(parsed, dict):
        raise ValueError("energy charts payload must be an object")
    return parsed
