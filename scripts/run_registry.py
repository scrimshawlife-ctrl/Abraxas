#!/usr/bin/env python3
"""run_registry.py

Loads the rune registry and emits a validation summary.
Governance-first, projection-only output.
"""
from __future__ import annotations

import json
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


def _find_registry() -> dict:
    """Locate and load the rune registry."""
    candidates = [
        os.path.join(_REPO_ROOT, "abraxas", "runes", "registry.json"),
        os.path.join(_REPO_ROOT, "abraxas_ase", "runes", "catalog.v0.yaml"),
    ]
    for path in candidates:
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                if path.endswith(".json"):
                    return json.load(fh)
                else:
                    return {"path": path, "loaded": True}
    return {}


def main() -> int:
    print("[run_registry] loading rune registry")
    registry = _find_registry()
    rune_count = len(registry.get("runes", registry.get("capabilities", [])))
    print(f"  registry entries    : {rune_count}")
    print("[run_registry] complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
