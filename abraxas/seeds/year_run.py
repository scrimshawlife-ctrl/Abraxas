"""Deterministic year-run seedpack generator (v0.2)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

from abraxas.runes.ctx import RuneInvocationContext
from abraxas.runes.invoke import invoke_capability
from abraxas.seeds.emit_seedpack import emit_seedpack
from abraxas.policy.utp import load_active_utp
from abraxas.runtime.concurrency import ConcurrencyConfig
from abraxas.runtime.deterministic_executor import commit_results, execute_parallel, WorkResult
from abraxas.runtime.work_units import WorkUnit


@dataclass(frozen=True)
class YearRunConfig:
    year: int
    window: str
    out_path: Path
    cache_dir: Path
    offline: bool = True
    include_linguistic: bool = False
    include_economics: bool = False
    include_governance: bool = False


def _load_packets(cache_dir: Path) -> List[Dict[str, Any]]:
    packets: List[Dict[str, Any]] = []
    if not cache_dir.exists():
        return packets
    for path in sorted(cache_dir.glob("*.json")):
        packets.append(json.loads(path.read_text(encoding="utf-8")))
    return packets


def _weekly_windows(year: int) -> List[Dict[str, str]]:
    start = datetime(year, 1, 1, tzinfo=timezone.utc)
    windows = []
    current = start
    while current.year == year:
        end = current + timedelta(days=7)
        window = {
            "start": current.isoformat().replace("+00:00", "Z"),
            "end": end.isoformat().replace("+00:00", "Z"),
        }
        windows.append(window)
        current = end
    return windows


def run_year(config: YearRunConfig) -> Dict[str, Any]:
    packets = _load_packets(config.cache_dir)
    if not config.include_linguistic:
        packets = [packet for packet in packets if not str(packet.get("source_id", "")).startswith("LINGUISTIC_")]
    if not config.include_economics:
        packets = [packet for packet in packets if not str(packet.get("source_id", "")).startswith("ECON_")]
    if not config.include_governance:
        packets = [packet for packet in packets if not str(packet.get("source_id", "")).startswith("GOV_")]
    windows = _weekly_windows(config.year)
    ctx = RuneInvocationContext(run_id=f"year_run_{config.year}", subsystem_id="seed", git_hash="unknown")

    portfolio = load_active_utp()
    concurrency = ConcurrencyConfig.from_portfolio(portfolio)
    work_units = _build_window_units(config.year, windows)
    results = execute_parallel(
        work_units,
        config=concurrency,
        stage="PARSE",
        handler=lambda unit: _process_window_unit(unit, packets, ctx),
    )
    committed = commit_results(results.results)

    frames: List[Dict[str, Any]] = []
    for result in committed:
        frames.extend(result.output_refs.get("frames") or [])

    influence_frames = [_flatten_frame(frame) for frame in frames]
    influence = invoke_capability("rune:influence_detect", {"frames": influence_frames}, ctx=ctx)
    synchronicity = invoke_capability("rune:synchronicity_map", {"frames": influence_frames}, ctx=ctx)

    return emit_seedpack(
        year=config.year,
        frames=frames,
        influence=influence,
        synchronicity=synchronicity,
        out_path=config.out_path,
    )


def _flatten_frame(frame: Dict[str, Any]) -> Dict[str, Any]:
    vectors = frame.get("vectors") or {}
    flattened = {}
    for key, value in vectors.items():
        if isinstance(value, dict):
            flattened[key] = value.get("score")
        else:
            flattened[key] = value
    return {
        "window_start_utc": frame.get("window_start_utc"),
        "window_end_utc": frame.get("window_end_utc"),
        "vectors": flattened,
        "provenance": frame.get("provenance") or {},
    }


def _build_window_units(year: int, windows: List[Dict[str, str]]) -> List[WorkUnit]:
    units: List[WorkUnit] = []
    for window in windows:
        key = (year, window["start"], window["end"])
        unit = WorkUnit.build(
            stage="PARSE",
            source_id="seedpack",
            window_utc=window,
            key=key,
            input_refs={"window": window},
            input_bytes=0,
        )
        units.append(unit)
    return sorted(units, key=lambda unit: unit.key)


def _process_window_unit(unit: WorkUnit, packets: List[Dict[str, Any]], ctx: RuneInvocationContext) -> WorkResult:
    window = unit.input_refs.get("window") or {}
    window_packets = [
        packet
        for packet in packets
        if (packet.get("window_start_utc") or "") <= window.get("end", "")
        and (packet.get("window_end_utc") or "") >= window.get("start", "")
    ]
    metrics = invoke_capability("rune:metric_extract", {"packets": window_packets}, ctx=ctx)
    tvm_frame = invoke_capability(
        "rune:tvm_frame",
        {
            "metrics": metrics.get("metrics") or [],
            "window_start_utc": window.get("start"),
            "window_end_utc": window.get("end"),
        },
        ctx=ctx,
    )
    return WorkResult(
        unit_id=unit.unit_id,
        key=unit.key,
        output_refs={"frames": tvm_frame.get("frames") or []},
        bytes_processed=0,
        stage=unit.stage,
    )


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run deterministic year seedpack generation (v0.2)")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--window", default="weekly")
    parser.add_argument("--out", required=True)
    parser.add_argument("--cache-dir", default="data/source_packets/2025")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--include-linguistic", action="store_true")
    parser.add_argument("--include-economics", action="store_true")
    parser.add_argument("--include-governance", action="store_true")
    args = parser.parse_args()

    config = YearRunConfig(
        year=args.year,
        window=args.window,
        out_path=Path(args.out),
        cache_dir=Path(args.cache_dir),
        offline=args.offline,
        include_linguistic=args.include_linguistic,
        include_economics=args.include_economics,
        include_governance=args.include_governance,
    )
    run_year(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
