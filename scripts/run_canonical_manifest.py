#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abx.governance.canonical_manifest import build_canonical_manifest, manifest_diff_against_frozen


if __name__ == "__main__":
    print(
        json.dumps(
            {
                "manifest": build_canonical_manifest().__dict__,
                "diff": manifest_diff_against_frozen(),
            },
            indent=2,
            sort_keys=True,
        )
    )
