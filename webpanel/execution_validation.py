from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


def _safe_read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def load_execution_validation_for_run(
    run_id: str,
    *,
    validators_dir: Path = Path("out/validators"),
) -> Optional[Dict[str, Any]]:
    """
    Load execution validation artifact for a run.

    Resolution strategy (deterministic):
      1) Exact artifact filename: execution-validation-<run_id>.json
      2) Scan validators dir and match payload["runId"] == run_id
    """
    exact = validators_dir / f"execution-validation-{run_id}.json"
    if exact.exists():
        payload = _safe_read_json(exact)
        if payload:
            payload.setdefault("_source_path", exact.as_posix())
            return payload

    if not validators_dir.exists():
        return None

    for path in sorted(validators_dir.glob("*.json")):
        payload = _safe_read_json(path)
        if not payload:
            continue
        if str(payload.get("runId", "")) != run_id:
            continue
        payload.setdefault("_source_path", path.as_posix())
        return payload
    return None

