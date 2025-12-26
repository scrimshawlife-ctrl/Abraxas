from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional


def enforce_non_truncation(
    *,
    artifact: Dict[str, Any],
    raw_full: Any,
    raw_full_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Enforce NT-0: always preserve full raw output.
    If raw_full_path is provided, raw_full is written to disk and referenced.
    Otherwise raw_full is embedded.
    """
    out = dict(artifact)
    out.setdefault("policy", {})
    out["policy"]["non_truncation"] = True

    if raw_full_path:
        os.makedirs(os.path.dirname(raw_full_path), exist_ok=True)
        with open(raw_full_path, "w", encoding="utf-8") as f:
            if isinstance(raw_full, (dict, list)):
                json.dump(raw_full, f, ensure_ascii=False, indent=2)
            else:
                f.write(str(raw_full))
        out["raw_full_path"] = raw_full_path
    else:
        out["raw_full"] = raw_full

    out.setdefault("views", {})
    out.setdefault("flags", [])
    out.setdefault("metrics", {})
    return out
