from __future__ import annotations

from datetime import datetime, timezone
import os
import hashlib
import json
from typing import Any, Dict


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


DRIFT_PAUSE_THRESHOLD = _env_int("ABX_DRIFT_PAUSE_THRESHOLD", 3)
MAX_DIFF_PATHS = _env_int("ABX_MAX_DIFF_PATHS", 200)
MAX_DIFF_METRICS = _env_int("ABX_MAX_DIFF_METRICS", 100)
MAX_DIFF_REFS = _env_int("ABX_MAX_DIFF_REFS", 100)
MAX_DIFF_UNKNOWNS = _env_int("ABX_MAX_DIFF_UNKNOWNS", 100)


def _canonical_json_bytes(obj: Any) -> bytes:
    rendered = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return rendered.encode("utf-8")


def compute_policy_hash(snapshot: Dict[str, Any]) -> str:
    snapshot_no_ts = {
        k: v
        for k, v in snapshot.items()
        if k not in {"timestamp_utc", "policy_hash"}
    }
    return hashlib.sha256(_canonical_json_bytes(snapshot_no_ts)).hexdigest()


def get_policy_snapshot() -> Dict[str, Any]:
    host = os.environ.get("ABX_PANEL_HOST", "127.0.0.1")
    port = os.environ.get("ABX_PANEL_PORT", "8008")
    token_enabled = bool(os.environ.get("ABX_PANEL_TOKEN", "").strip())
    snapshot = {
        "kind": "PolicySnapshot.v0",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "thresholds": {"drift_pause_threshold": DRIFT_PAUSE_THRESHOLD},
        "caps": {
            "max_diff_paths": MAX_DIFF_PATHS,
            "max_diff_metrics": MAX_DIFF_METRICS,
            "max_diff_refs": MAX_DIFF_REFS,
            "max_diff_unknowns": MAX_DIFF_UNKNOWNS,
        },
        "runtime": {"host": host, "port": port, "token_enabled": token_enabled},
    }
    snapshot["policy_hash"] = compute_policy_hash(snapshot)
    return snapshot


def policy_snapshot() -> Dict[str, Any]:
    return get_policy_snapshot()
