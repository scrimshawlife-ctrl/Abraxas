"""Abraxas CLI dispatcher."""

from __future__ import annotations

import argparse

from abraxas.cli.atlas import run_atlas_cmd
from abraxas.cli.atlas_delta import run_atlas_delta_cmd
from abraxas.cli.live import run_live_cmd
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

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
