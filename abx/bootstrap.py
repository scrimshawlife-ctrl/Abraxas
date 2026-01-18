"""Bootstrap hooks for deterministic dependency resolution."""

from __future__ import annotations

import sys
from pathlib import Path


def _vendor_pyyaml() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    vendor_path = repo_root / "vendor" / "pyyaml"
    if vendor_path.exists():
        sys.path.insert(0, str(vendor_path))


_vendor_pyyaml()
