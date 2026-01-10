from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import VERSION
from .export.bundle import export_bundle
from .ingest import ingest_file
from .queue.review import apply_review
from .queue.states import QueueState
from .storage import list_queue_items


def main() -> None:
    parser = argparse.ArgumentParser(prog="aatf", description="Abraxas Admin & Training Forge")
    parser.add_argument("--version", action="version", version=VERSION)
    sub = parser.add_subparsers(dest="cmd", required=True)

    ingest_cmd = sub.add_parser("ingest", help="Ingest a file")
    ingest_cmd.add_argument("path")
    ingest_cmd.add_argument("--kind", default="auto", choices=["auto", "txt", "md", "json", "pdf"])
    ingest_cmd.add_argument("--tag", action="append", default=[])

    queue_cmd = sub.add_parser("queue", help="Queue operations")
    queue_sub = queue_cmd.add_subparsers(dest="queue_action", required=True)
    queue_list = queue_sub.add_parser("list", help="List queue items")
    queue_list.add_argument("--state", default=None, choices=[s.value for s in QueueState])

    review_cmd = sub.add_parser("review", help="Review queue items")
    review_sub = review_cmd.add_subparsers(dest="review_action", required=True)
    approve_cmd = review_sub.add_parser("approve", help="Approve item")
    approve_cmd.add_argument("item_id")
    approve_cmd.add_argument("--notes", required=True)
    reject_cmd = review_sub.add_parser("reject", help="Reject item")
    reject_cmd.add_argument("item_id")
    reject_cmd.add_argument("--notes", required=True)

    export_cmd = sub.add_parser("export", help="Export bundles")
    export_sub = export_cmd.add_subparsers(dest="export_action", required=True)
    bundle_cmd = export_sub.add_parser("bundle", help="Export deterministic bundle")
    bundle_cmd.add_argument("--types", default="aalmanac,memetic_weather,neon_genie,rune_proposals")
    bundle_cmd.add_argument("--out", default=None)

    args = parser.parse_args()

    if args.cmd == "ingest":
        result = ingest_file(args.path, args.tag, kind=args.kind)
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result.get("status") == "ok" else 2)

    if args.cmd == "queue" and args.queue_action == "list":
        items = list_queue_items(state=args.state)
        print(json.dumps({"items": items}, indent=2))
        raise SystemExit(0)

    if args.cmd == "review":
        if args.review_action == "approve":
            result = apply_review(args.item_id, QueueState.APPROVED, args.notes)
            print(json.dumps(result, indent=2))
            raise SystemExit(0)
        if args.review_action == "reject":
            result = apply_review(args.item_id, QueueState.REJECTED, args.notes)
            print(json.dumps(result, indent=2))
            raise SystemExit(0)

    if args.cmd == "export" and args.export_action == "bundle":
        types = [t.strip() for t in args.types.split(",") if t.strip()]
        result = export_bundle(types, out_path=args.out)
        print(json.dumps(result, indent=2))
        raise SystemExit(0)

    raise SystemExit(2)


if __name__ == "__main__":
    main()
