#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from abraxas.viz.frontend_harness_manifest import build_manifest


def main() -> None:
    root = Path("frontend/aal-viz")
    manifest = build_manifest(root)
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
