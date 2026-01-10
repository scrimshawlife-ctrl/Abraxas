from __future__ import annotations

import argparse
from aatf.api import ingest_payload, export_bundle


def main() -> int:
    ap = argparse.ArgumentParser(prog="aatf")
    ap.add_argument("--ingest", help="Path to payload JSON to ingest")
    ap.add_argument("--export", help="Output directory for export bundle")
    args = ap.parse_args()

    if args.ingest:
        ingest_payload(args.ingest)
    if args.export:
        export_bundle(args.export)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
