from __future__ import annotations

from pathlib import Path
from typing import Any

from .runtime import write_canonical_json


def emit_artifact(path: Path, payload: dict[str, Any]) -> str:
    return write_canonical_json(path, payload)
