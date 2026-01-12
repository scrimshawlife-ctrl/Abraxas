"""Export GRIM overlay delta for Abraxas runes."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from abraxas.grim_bridge import registry_size, write_overlay_delta


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Abraxas GRIM overlay delta JSON")
    parser.add_argument(
        "--output",
        default=Path(".aal/grim/abx_grim.overlay_delta.json"),
        type=Path,
        help="Output path for overlay delta JSON",
    )
    args = parser.parse_args()

    if registry_size() == 0:
        print("No runes registered; refusing to export overlay delta.", file=sys.stderr)
        return 1

    write_overlay_delta(args.output)
    print(f"Wrote overlay delta to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
