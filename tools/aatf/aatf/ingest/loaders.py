from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json


def load_json_payload(path: str) -> Dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("payload must be a JSON object")
    return data
