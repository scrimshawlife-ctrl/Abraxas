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
from abraxas.sources.domain_map import domain_for_source_id


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
    allow_simulated: bool = False


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
    if not config.allow_simulated:
        filtered = []
        for packet in packets:
            grade = str(packet.get("data_grade") or (packet.get("provenance") or {}).get("data_grade") or "real")
            if grade == "simulated":
                continue
            filtered.append(packet)
        packets = filtered
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
    coverage: List[Dict[str, Any]] = []
    for result in committed:
        frames.extend(result.output_refs.get("frames") or [])
        coverage.extend(result.output_refs.get("coverage") or [])

    influence_frames = [_flatten_frame(frame) for frame in frames]
    influence = invoke_capability("rune:influence_detect", {"frames": influence_frames}, ctx=ctx)
    synchronicity = invoke_capability("rune:synchronicity_map", {"frames": influence_frames}, ctx=ctx)

    return emit_seedpack(
        year=config.year,
        frames=frames,
        influence=influence,
        synchronicity=synchronicity,
        coverage=coverage,
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
        "domain": frame.get("domain") or "unknown",
        "data_grade": frame.get("data_grade") or "real",
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
    packets_by_domain: Dict[str, int] = {}
    packets_by_source: Dict[str, int] = {}
    for packet in window_packets:
        source_id = str(packet.get("source_id") or "unknown")
        domain = str(
            packet.get("domain")
            or (packet.get("provenance") or {}).get("domain")
            or domain_for_source_id(source_id)
        )
        packets_by_domain[domain] = packets_by_domain.get(domain, 0) + 1
        packets_by_source[source_id] = packets_by_source.get(source_id, 0) + 1
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
    coverage_items: List[Dict[str, Any]] = []
    for frame in tvm_frame.get("frames") or []:
        domain = str(frame.get("domain") or "unknown")
        vectors = frame.get("vectors") or {}
        computed = 0
        not_computable = 0
        reasons: List[str] = []
        for value in vectors.values():
            if isinstance(value, dict) and value.get("computability") == "computed":
                computed += 1
            elif isinstance(value, dict) and value.get("computability") == "not_computable":
                not_computable += 1
                note = value.get("notes")
                if isinstance(note, str) and note:
                    reasons.append(note)
        coverage_items.append(
            {
                "window_start_utc": window.get("start"),
                "window_end_utc": window.get("end"),
                "domain": domain,
                "packets_seen": packets_by_domain.get(domain, 0),
                "vectors_computed": computed,
                "vectors_not_computable": not_computable,
                "not_computable_reasons": sorted(set(reasons)),
                "packets_by_source": {key: packets_by_source[key] for key in sorted(packets_by_source.keys())},
            }
        )
    return WorkResult(
        unit_id=unit.unit_id,
        key=unit.key,
        output_refs={"frames": tvm_frame.get("frames") or [], "coverage": coverage_items},
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
    parser.add_argument("--allow-simulated", action="store_true", help="Allow packets marked data_grade=simulated")
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
        allow_simulated=args.allow_simulated,
    )
    run_year(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
