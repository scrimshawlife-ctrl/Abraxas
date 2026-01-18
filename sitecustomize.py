"""Site customization for deterministic vendored dependencies."""

from __future__ import annotations

import sys
from pathlib import Path


def _prepend_vendor() -> None:
    repo_root = Path(__file__).resolve().parent
    vendor_path = repo_root / "vendor" / "pyyaml"
    if vendor_path.exists():
        sys.path.insert(0, str(vendor_path))


_prepend_vendor()
