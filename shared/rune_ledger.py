# Rune Invocation Ledger (v0.1) — append-only JSONL

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

DEFAULT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "rune_invocations.jsonl"
)


def _stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def record_invocation(
    *,
    rune_id: str,
    payload: Dict[str, Any],
    provenance_bundle: Dict[str, Any],
    callsite: Optional[Dict[str, Any]] = None,
    path: Optional[str] = None,
) -> Dict[str, Any]:
    lp = path or DEFAULT_PATH
    os.makedirs(os.path.dirname(lp), exist_ok=True)

    ts = datetime.now(timezone.utc).isoformat()
    core = {
        "timestamp_utc": ts,
        "rune_id": rune_id,
        "payload_sha256": _sha256(_stable_json(payload)),
        "repo_commit": provenance_bundle.get("repo_commit", "unknown"),
    }
    inv_id = _sha256(_stable_json(core))

    rec = {
        "invocation_id": inv_id,
        "timestamp_utc": ts,
        "rune_id": rune_id,
        "payload_sha256": core["payload_sha256"],
        "repo_commit": core["repo_commit"],
        "callsite": callsite or {},
        "provenance_bundle": provenance_bundle,
    }

    with open(lp, "a", encoding="utf-8") as file:
        file.write(_stable_json(rec) + "\n")

    return rec
