"""Abraxas CLI dispatcher."""

from __future__ import annotations

import argparse

from abraxas.cli.atlas import run_atlas_cmd
from abraxas.cli.atlas_delta import run_atlas_delta_cmd
from abraxas.cli.manifest import run_bulk_plan, run_execute_plan, run_manifest_discovery
from abraxas.cli.live import run_live_cmd
from abraxas.cli.profile import run_profile_command, run_profile_ingest
from abraxas.cli.device import run_device_apply, run_device_detect, run_device_list, run_device_select
from abraxas.cli.storage import (
    run_storage_compact,
    run_storage_execute,
    run_storage_plan,
    run_storage_revert,
    run_storage_summarize,
)
from abraxas.cli.seed import run_seed
from abraxas.cli.sonify import run_sonify_cmd
from abraxas.cli.sources import list_sources_cmd
from abraxas.cli.temporal import tzdb_version_cmd
from abraxas.cli.visualize import run_visualize_cmd
from abraxas.cli.year_run import run_year_cmd


def main() -> int:
    parser = argparse.ArgumentParser(prog="abraxas", description="Abraxas CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    seed_parser = subparsers.add_parser("seed", help="Generate seed packs")
    seed_parser.add_argument("--year", type=int, required=True, help="Seed pack year")
    seed_parser.add_argument("--out", required=True, help="Output path")

    sources_parser = subparsers.add_parser("sources", help="SourceAtlas commands")
    sources_sub = sources_parser.add_subparsers(dest="sources_cmd", required=True)
    sources_sub.add_parser("list", help="List SourceAtlas entries")

    temporal_parser = subparsers.add_parser("temporal", help="Temporal suite commands")
    temporal_sub = temporal_parser.add_subparsers(dest="temporal_cmd", required=True)
    temporal_sub.add_parser("tzdb-version", help="Print TZDB snapshot version")

    year_run_parser = subparsers.add_parser("year-run", help="Generate yearly seedpack")
    year_run_parser.add_argument("--year", type=int, required=True)
    year_run_parser.add_argument("--window", default="weekly")
    year_run_parser.add_argument("--out", required=True)
    year_run_parser.add_argument("--cache-dir", default="data/source_packets/2025")
    year_run_parser.add_argument("--offline", action="store_true")
    year_run_parser.add_argument("--include-linguistic", action="store_true")
    year_run_parser.add_argument("--include-economics", action="store_true")
    year_run_parser.add_argument("--include-governance", action="store_true")

    atlas_parser = subparsers.add_parser("atlas", help="Generate semantic weather atlas")
    atlas_parser.add_argument("--year", type=int, required=True)
    atlas_parser.add_argument("--window", default="weekly")
    atlas_parser.add_argument("--seed", required=True, help="Seedpack path")
    atlas_parser.add_argument("--out", required=True, help="Atlas output path")
    atlas_parser.add_argument("--trendpack-out", help="Trendpack output path")
    atlas_parser.add_argument("--chronoscope-out", help="Chronoscope output path")

    atlas_delta_parser = subparsers.add_parser("atlas-delta", help="Generate delta atlas pack")
    atlas_delta_parser.add_argument("--base", required=True, help="Base atlas path")
    atlas_delta_parser.add_argument("--compare", required=True, help="Compare atlas path")
    atlas_delta_parser.add_argument("--label", required=True, help="Comparison label (e.g. 2024→2025)")
    atlas_delta_parser.add_argument("--out", required=True, help="Delta atlas output path")
    atlas_delta_parser.add_argument("--trendpack-out", help="Delta trendpack output path")

    live_parser = subparsers.add_parser("live", help="Generate live atlas packs")
    live_parser.add_argument("--window-size", required=True, help="Window size (e.g. 7d)")
    live_parser.add_argument("--step", required=True, help="Step size (e.g. 1d)")
    live_parser.add_argument("--retention", type=int, default=30, help="Number of windows to retain")
    live_parser.add_argument("--out", required=True, help="Output path")
    live_parser.add_argument("--cache-dir", default="data/source_packets/2025")
    live_parser.add_argument("--now", help="Override current time (UTC ISO8601)")
    live_parser.add_argument("--snapshot", action="store_true", help="Emit latest snapshot only")
    live_parser.add_argument("--trendpack-out", help="Live trendpack output path")

    sonify_parser = subparsers.add_parser("sonify", help="Generate audio control frames from atlas")
    sonify_parser.add_argument("--atlas", required=True, help="Atlas pack path")
    sonify_parser.add_argument("--out", required=True, help="Output path for control frames")

    visualize_parser = subparsers.add_parser("visualize", help="Generate visual control frames from atlas")
    visualize_parser.add_argument("--atlas", required=True, help="Atlas pack path")
    visualize_parser.add_argument("--out", required=True, help="Output path for control frames")

    manifest_parser = subparsers.add_parser("manifest", help="Manifest discovery (manifest-first)")
    manifest_parser.add_argument("--source", required=True, help="Source ID")
    manifest_parser.add_argument("--out", required=True, help="Output path for manifest JSON")
    manifest_parser.add_argument("--seed", action="append", help="Seed URL (repeatable)")
    manifest_parser.add_argument("--now", help="Override current time (UTC ISO8601)")

    plan_parser = subparsers.add_parser("plan", help="Build bulk pull plan from manifest")
    plan_parser.add_argument("--source", required=True, help="Source ID")
    plan_parser.add_argument("--manifest", required=True, help="Manifest JSON path")
    plan_parser.add_argument("--out", required=True, help="Output path for bulk plan JSON")
    plan_parser.add_argument("--start", help="Window start (UTC ISO8601)")
    plan_parser.add_argument("--end", help="Window end (UTC ISO8601)")
    plan_parser.add_argument("--now", help="Override current time (UTC ISO8601)")

    exec_parser = subparsers.add_parser("execute-plan", help="Execute bulk plan (bulk/cache only)")
    exec_parser.add_argument("--plan", required=True, help="Bulk plan JSON path")
    exec_parser.add_argument("--offline", action="store_true", help="Use cache-only execution")
    exec_parser.add_argument("--online", action="store_true", help="Force online execution")
    exec_parser.add_argument("--out", help="Output path for execution results")
    exec_parser.add_argument("--now", help="Override current time (UTC ISO8601)")

    storage_parser = subparsers.add_parser("storage", help="Storage lifecycle commands")
    storage_sub = storage_parser.add_subparsers(dest="storage_cmd", required=True)
    summarize_parser = storage_sub.add_parser("summarize", help="Summarize storage index")
    summarize_parser.add_argument("--index", required=True, help="Storage index JSONL path")
    summarize_parser.add_argument("--now", help="Override current time (UTC ISO8601)")

    storage_plan_parser = storage_sub.add_parser("plan", help="Plan storage lifecycle")
    storage_plan_parser.add_argument("--index", required=True, help="Storage index JSONL path")
    storage_plan_parser.add_argument("--out", required=True, help="Output path for lifecycle plan")
    storage_plan_parser.add_argument("--now", help="Override current time (UTC ISO8601)")
    storage_plan_parser.add_argument("--allow-raw-delete", action="store_true", help="Allow raw deletion in plan")

    storage_exec_parser = storage_sub.add_parser("execute", help="Execute storage lifecycle plan")
    storage_exec_parser.add_argument("--plan", required=True, help="Lifecycle plan JSON path")
    storage_exec_parser.add_argument("--allow-raw-delete", action="store_true", help="Allow raw deletion")

    storage_compact_parser = storage_sub.add_parser("compact", help="Execute compaction-only plan")
    storage_compact_parser.add_argument("--plan", required=True, help="Lifecycle plan JSON path")
    storage_compact_parser.add_argument("--max-files", type=int, default=500)
    storage_compact_parser.add_argument("--max-cpu-ms", type=int, default=60000)

    storage_revert_parser = storage_sub.add_parser("revert", help="Revert lifecycle pointer")
    storage_revert_parser.add_argument("--pointer", required=True, help="Pointer file path")

    profile_parser = subparsers.add_parser("profile", help="Hardware profile commands")
    profile_sub = profile_parser.add_subparsers(dest="profile_cmd", required=True)
    profile_run_parser = profile_sub.add_parser("run", help="Run profiling suite")
    profile_run_parser.add_argument("--suite", default="orin", help="Suite name")
    profile_run_parser.add_argument("--windows", type=int, default=12)
    profile_run_parser.add_argument("--repetitions", type=int, default=5)
    profile_run_parser.add_argument("--warmup", type=int, default=1)
    profile_run_parser.add_argument("--offline", action="store_true")
    profile_run_parser.add_argument("--now", help="Override current time (UTC ISO8601)")
    profile_run_parser.add_argument("--out", required=True, help="Output ProfilePack path")
    profile_run_parser.add_argument("--pin-clocks", action="store_true")

    profile_ingest_parser = profile_sub.add_parser("ingest", help="Ingest ProfilePack")
    profile_ingest_parser.add_argument("--profile", required=True, help="ProfilePack JSON path")

    device_parser = subparsers.add_parser("device", help="Device profile commands")
    device_sub = device_parser.add_subparsers(dest="device_cmd", required=True)
    device_sub.add_parser("list", help="List device profiles")
    detect_parser = device_sub.add_parser("detect", help="Detect device fingerprint")
    detect_parser.add_argument("--now", help="Override current time (UTC ISO8601)")
    select_parser = device_sub.add_parser("select", help="Select device profile")
    select_parser.add_argument("--now", help="Override current time (UTC ISO8601)")
    select_parser.add_argument("--dry-run", action="store_true")
    apply_parser = device_sub.add_parser("apply", help="Apply device profile selection")
    apply_parser.add_argument("--now", help="Override current time (UTC ISO8601)")

    args = parser.parse_args()

    if args.command == "seed":
        return run_seed(args.year, args.out)
    if args.command == "sources":
        if args.sources_cmd == "list":
            return list_sources_cmd()
    if args.command == "temporal":
        if args.temporal_cmd == "tzdb-version":
            return tzdb_version_cmd()
    if args.command == "year-run":
        return run_year_cmd(
            args.year,
            args.window,
            args.out,
            args.cache_dir,
            args.offline,
            args.include_linguistic,
            args.include_economics,
            args.include_governance,
        )
    if args.command == "atlas":
        return run_atlas_cmd(
            args.year,
            args.window,
            args.seed,
            args.out,
            args.trendpack_out,
            args.chronoscope_out,
        )
    if args.command == "atlas-delta":
        return run_atlas_delta_cmd(
            args.base,
            args.compare,
            args.out,
            args.label,
            args.trendpack_out,
        )
    if args.command == "live":
        return run_live_cmd(
            args.window_size,
            args.step,
            args.retention,
            args.out,
            args.cache_dir,
            args.now,
            args.snapshot,
            args.trendpack_out,
        )
    if args.command == "sonify":
        return run_sonify_cmd(args.atlas, args.out)
    if args.command == "visualize":
        return run_visualize_cmd(args.atlas, args.out)
    if args.command == "manifest":
        return run_manifest_discovery(args.source, args.out, args.seed, args.now)
    if args.command == "plan":
        return run_bulk_plan(args.source, args.manifest, args.out, args.start, args.end, args.now)
    if args.command == "execute-plan":
        offline = args.offline
        if args.online:
            offline = False
        return run_execute_plan(args.plan, offline, args.out, args.now)
    if args.command == "storage":
        if args.storage_cmd == "summarize":
            return run_storage_summarize(args.index, args.now)
        if args.storage_cmd == "plan":
            return run_storage_plan(args.index, args.out, args.now, args.allow_raw_delete)
        if args.storage_cmd == "execute":
            return run_storage_execute(args.plan, args.allow_raw_delete)
        if args.storage_cmd == "compact":
            return run_storage_compact(args.plan, args.max_files, args.max_cpu_ms)
        if args.storage_cmd == "revert":
            return run_storage_revert(args.pointer)
    if args.command == "profile":
        if args.profile_cmd == "run":
            return run_profile_command(
                suite=args.suite,
                windows=args.windows,
                repetitions=args.repetitions,
                warmup=args.warmup,
                offline=args.offline,
                now=args.now,
                out_path=args.out,
                pin_clocks=args.pin_clocks,
            )
        if args.profile_cmd == "ingest":
            return run_profile_ingest(args.profile)
    if args.command == "device":
        if args.device_cmd == "list":
            return run_device_list()
        if args.device_cmd == "detect":
            return run_device_detect(args.now)
        if args.device_cmd == "select":
            return run_device_select(args.now, args.dry_run)
        if args.device_cmd == "apply":
            return run_device_apply(args.now)

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
