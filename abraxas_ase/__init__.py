from __future__ import annotations

import sys
from pathlib import Path

_VENDORED_PYYAML = Path(__file__).resolve().parent.parent / "vendor" / "pyyaml"
if _VENDORED_PYYAML.exists():
    vendored_path = str(_VENDORED_PYYAML)
    if vendored_path not in sys.path:
        sys.path.insert(0, vendored_path)

__all__ = ["__version__"]
__version__ = "0.1.0"
