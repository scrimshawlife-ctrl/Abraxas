#!/usr/bin/env python3
"""
Deterministic artifact retention for Abraxas.

Usage:
    # Enable retention and keep last 200 ticks
    python -m scripts.prune_artifacts --artifacts_dir ./artifacts --run_id <RUN_ID> --enable --keep_last 200

    # Add byte cap (200MB)
    python -m scripts.prune_artifacts --artifacts_dir ./artifacts --run_id <RUN_ID> --enable --keep_last 200 --max_bytes 200000000

    # Disable retention
    python -m scripts.prune_artifacts --artifacts_dir ./artifacts --run_id <RUN_ID> --disable

    # Prune all runs
    python -m scripts.prune_artifacts --artifacts_dir ./artifacts --all --enable --keep_last 100

    # Show stats only (no pruning)
    python -m scripts.prune_artifacts --artifacts_dir ./artifacts --run_id <RUN_ID> --stats

This will:
- Keep last N ticks (by tick number)
- Enforce byte cap by deleting oldest kept artifacts first (deterministic)
- Compact the manifest so it only lists existing files
- Never delete manifests/ or policy/ directories
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from abraxas.runtime.retention import ArtifactPruner, PruneReport


def _print_json(obj: dict) -> None:
    """Print JSON deterministically."""
    print(json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Deterministic artifact retention for Abraxas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument(
        "--artifacts_dir",
        required=True,
        help="Path to artifacts directory",
    )
    ap.add_argument(
        "--run_id",
        help="Run ID to prune (required unless --all or --list)",
    )
    ap.add_argument(
        "--all",
        action="store_true",
        help="Prune all discovered run IDs",
    )
    ap.add_argument(
        "--list",
        action="store_true",
        help="List all discovered run IDs",
    )
    ap.add_argument(
        "--stats",
        action="store_true",
        help="Show stats only (no pruning)",
    )
    ap.add_argument(
        "--enable",
        action="store_true",
        help="Enable retention in policy",
    )
    ap.add_argument(
        "--disable",
        action="store_true",
        help="Disable retention in policy",
    )
    ap.add_argument(
        "--keep_last",
        type=int,
        default=None,
        help="Keep last N ticks per run_id",
    )
    ap.add_argument(
        "--max_bytes",
        type=int,
        default=None,
        help="Maximum bytes per run_id (optional)",
    )
    ap.add_argument(
        "--no_compact",
        action="store_true",
        help="Skip manifest compaction after prune",
    )
    ap.add_argument(
        "--dry_run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )

    args = ap.parse_args()

    # Validate arguments
    if not args.list and not args.all and not args.run_id:
        ap.error("--run_id is required unless --all or --list is specified")

    if args.enable and args.disable:
        ap.error("Cannot specify both --enable and --disable")

    pruner = ArtifactPruner(args.artifacts_dir)

    # Handle --list
    if args.list:
        run_ids = pruner.discover_run_ids()
        _print_json({
            "ok": True,
            "run_ids": run_ids,
            "count": len(run_ids),
        })
        return 0

    # Load and update policy
    policy = pruner.load_policy()

    if args.enable:
        policy["enabled"] = True
    if args.disable:
        policy["enabled"] = False
    if args.keep_last is not None:
        policy["keep_last_ticks"] = int(args.keep_last)
    if args.max_bytes is not None:
        policy["max_bytes_per_run"] = int(args.max_bytes)
    if args.no_compact:
        policy["compact_manifest"] = False

    # Save updated policy
    pruner.save_policy(policy)

    # Handle --stats
    if args.stats:
        if args.all:
            stats = []
            for run_id in pruner.discover_run_ids():
                stats.append(pruner.get_run_stats(run_id))
            _print_json({
                "ok": True,
                "stats": stats,
                "policy": policy,
            })
        else:
            stats = pruner.get_run_stats(args.run_id)
            _print_json({
                "ok": True,
                "stats": stats,
                "policy": policy,
            })
        return 0

    # Handle --dry_run (for now, just show policy)
    if args.dry_run:
        if args.all:
            run_ids = pruner.discover_run_ids()
        else:
            run_ids = [args.run_id]

        dry_info = []
        for run_id in run_ids:
            stats = pruner.get_run_stats(run_id)
            keep_last = policy.get("keep_last_ticks", 200)
            would_delete_ticks = max(0, stats["tick_count"] - keep_last)
            dry_info.append({
                "run_id": run_id,
                "current_ticks": stats["tick_count"],
                "current_bytes": stats["total_bytes"],
                "would_keep_ticks": min(stats["tick_count"], keep_last),
                "would_delete_ticks": would_delete_ticks,
            })

        _print_json({
            "ok": True,
            "dry_run": True,
            "info": dry_info,
            "policy": policy,
        })
        return 0

    # Execute prune
    reports: List[PruneReport]
    if args.all:
        reports = pruner.prune_all(policy=policy)
    else:
        reports = [pruner.prune_run(args.run_id, policy=policy)]

    # Format output
    results = []
    for rep in reports:
        results.append({
            "run_id": rep.run_id,
            "kept_ticks": rep.kept_ticks,
            "kept_tick_count": len(rep.kept_ticks),
            "deleted_files_count": len(rep.deleted_files),
            "deleted_bytes": rep.deleted_bytes,
        })

    total_deleted_files = sum(len(r.deleted_files) for r in reports)
    total_deleted_bytes = sum(r.deleted_bytes for r in reports)

    _print_json({
        "ok": True,
        "results": results,
        "total_deleted_files": total_deleted_files,
        "total_deleted_bytes": total_deleted_bytes,
        "policy": policy,
    })

    return 0


if __name__ == "__main__":
    sys.exit(main())
