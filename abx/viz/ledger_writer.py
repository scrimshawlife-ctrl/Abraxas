from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Optional


def write_aal_viz_proof_state_set(state_set: Mapping[str, Any], base_dir: Optional[Path] = None) -> Optional[str]:
    root = base_dir or Path("out")
    if not root.exists():
        return None
    target_dir = root / "viz"
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / "aal_viz_proof_state.jsonl"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(state_set), sort_keys=True) + "\n")
    return path.as_posix()
